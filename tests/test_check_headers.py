"""Unit tests for scripts/check_headers.py (standard library only)."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_headers  # noqa: E402


def make_headers(hashes=()):
    hash_tokens = " ".join(f"'{h}'" for h in hashes)
    script_src = f"'self' {hash_tokens}".strip()
    return (
        "/*\n"
        f"  Content-Security-Policy: default-src 'self'; script-src {script_src}; object-src 'none'; base-uri 'none'; frame-ancestors 'none'\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: no-referrer\n"
        "  X-Frame-Options: DENY\n"
        "  Permissions-Policy: camera=()\n"
    )


def run_check(folder):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = check_headers.main(["check_headers.py", str(folder)])
    return code, buf.getvalue()


def check_temp_site(html, hashes=()):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "_headers").write_text(make_headers(hashes), encoding="utf-8")
        (root / "index.html").write_text(html, encoding="utf-8")
        return run_check(root)


class InlineScriptsUnitTests(unittest.TestCase):
    def test_closing_tag_with_trailing_space(self):
        html = "<script>const x = 1;</script >"
        self.assertEqual(check_headers.inline_scripts(html), ["const x = 1;"])

    def test_uppercase_script_tags(self):
        html = "<SCRIPT>const y = 2;</SCRIPT>"
        self.assertEqual(check_headers.inline_scripts(html), ["const y = 2;"])

    def test_skips_scripts_with_src(self):
        html = (
            '<script src="app.js"></script>'
            '<script SRC="other.js">ignored()</script>'
            "<script>kept();</script>"
        )
        self.assertEqual(check_headers.inline_scripts(html), ["kept();"])

    def test_empty_inline_script_yields_empty_string(self):
        self.assertEqual(check_headers.inline_scripts("<script></script>"), [""])

    def test_preserves_raw_script_body_without_charref_decoding(self):
        body = "if (a < b && c > d) { const s = '&amp;'; }"
        self.assertEqual(check_headers.inline_scripts(f"<script>{body}</script>"), [body])

    def test_self_closing_script_tag_keeps_body(self):
        self.assertEqual(check_headers.inline_scripts("<script/>foo();</script>"), ["foo();"])
        self.assertEqual(check_headers.inline_scripts('<script src="a.js"/>bar();</script>'), [])

    def test_cdata_outside_foreign_content_ends_at_first_gt(self):
        html = "<!doctype html><body><![CDATA[><script>alert(1);</script>]]>"
        self.assertEqual(check_headers.inline_scripts(html), ["alert(1);"])

    def test_other_marked_section_ends_at_first_gt(self):
        html = "<![if x]><script>a();</script><![endif]>"
        self.assertEqual(check_headers.inline_scripts(html), ["a();"])

    def test_cdata_inside_svg_is_text(self):
        html = "<svg><![CDATA[<script>x();</script>]]></svg><script>y();</script>"
        self.assertEqual(check_headers.inline_scripts(html), ["y();"])


class CheckHeadersMainTests(unittest.TestCase):
    def test_inline_script_hash_present(self):
        body = "document.documentElement.classList.add('js');"
        code, out = check_temp_site(f"<script>{body}</script>", [check_headers.script_hash(body)])
        self.assertEqual(code, 0, out)
        self.assertIn("1 inline script(s)", out)

    def test_inline_script_hash_missing(self):
        code, out = check_temp_site("<script>alert(1);</script>")
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

    def test_closing_tag_with_space_detected_and_allowed_when_hashed(self):
        body = "alert(1);"
        html = f"<script>{body}</script >"

        code, out = check_temp_site(html)
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

        code, out = check_temp_site(html, [check_headers.script_hash(body)])
        self.assertEqual(code, 0, out)

    def test_self_closing_script_tag_detected_and_allowed_when_hashed(self):
        body = "foo();"
        html = f"<script/>{body}</script>"

        code, out = check_temp_site(html)
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

        code, out = check_temp_site(html, [check_headers.script_hash(body)])
        self.assertEqual(code, 0, out)

    def test_uppercase_script_missing_hash(self):
        code, out = check_temp_site("<SCRIPT>alert(1);</SCRIPT>")
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

    def test_external_script_ignored_with_no_hashes(self):
        code, out = check_temp_site('<script src="app.js"></script>')
        self.assertEqual(code, 0, out)
        self.assertIn("0 inline script(s)", out)

    def test_two_inline_scripts_both_or_one_hashed(self):
        b1, b2 = "first();", "second();"
        html = f"<script>{b1}</script><script>{b2}</script>"
        h1, h2 = check_headers.script_hash(b1), check_headers.script_hash(b2)

        code, out = check_temp_site(html, [h1, h2])
        self.assertEqual(code, 0, out)
        self.assertIn("2 inline script(s)", out)

        code, out = check_temp_site(html, [h1])
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

    def test_unused_policy_hash_prints_note(self):
        unused = check_headers.script_hash("neverUsed();")
        code, out = check_temp_site("<p>hello</p>", [unused])
        self.assertEqual(code, 0, out)
        self.assertIn("note: the policy lists a hash no page uses", out)

    def test_real_repo_site_folder_passes(self):
        site_dir = REPO_ROOT / "site"
        code, out = run_check(site_dir)
        self.assertEqual(code, 0, out)

    def test_script_after_cdata_declaration_needs_hash(self):
        html = "<!doctype html><body><![CDATA[><script>alert(1);</script>]]>"

        code, out = check_temp_site(html)
        self.assertEqual(code, 1)
        self.assertIn("inline script not in the policy", out)

        code, out = check_temp_site(html, [check_headers.script_hash("alert(1);")])
        self.assertEqual(code, 0, out)

    def test_ordinary_hashed_script_control(self):
        html = "<!doctype html><body><script>ok();</script>"
        code, out = check_temp_site(html, [check_headers.script_hash("ok();")])
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
