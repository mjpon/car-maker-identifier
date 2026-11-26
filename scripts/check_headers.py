"""Checks the security headers of a static site before it is published.

Usage:  python3 check_headers.py <folder that Cloudflare serves>

The folder has a file named _headers. This script checks that:
  - the main security headers are set,
  - the Content-Security-Policy does not allow inline or eval'd scripts, and
  - every inline <script> in the HTML files is listed in the policy by its hash.

If you change an inline <script>, the browser silently refuses to run it until its hash is in
the policy. This check catches that before you deploy. It prints the hash you need.
Standard library only.
"""

import base64
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REQUIRED = ["content-security-policy", "x-content-type-options", "referrer-policy", "x-frame-options", "permissions-policy"]


BREAKOUT_TAGS = frozenset(
    "b big blockquote body br center code dd div dl dt em embed h1 h2 h3 h4 h5 h6 head hr i img li listing menu meta nobr ol p pre ruby s small span strong strike sub sup table tt u ul var".split()
)
SVG_HTML_POINTS = frozenset({"foreignobject", "desc", "title"})
MATH_TEXT_POINTS = frozenset({"mi", "mo", "mn", "ms", "mtext"})


class InlineScripts(HTMLParser):
    """Collects the raw bodies of inline <script> elements (those without a src attribute).

    Tracks a stack of open SVG/MathML foreign elements, HTML integration points, and
    HTML breakout tags so foreign elements like <style> do not switch into raw-text
    mode and CDATA sections only apply inside foreign content.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self._chunks = None
        self._stack = []  # open foreign elements: (tag, namespace, is_html_point)
        self._foreign_start = False

    def _in_foreign(self):
        return bool(self._stack) and not self._stack[-1][2]

    def parse_html_declaration(self, i):
        # Real CDATA sections only apply inside foreign content; elsewhere (including
        # integration points) treat "<![..." as a bogus comment ending at the first ">".
        if self.rawdata.startswith("<![", i):
            if self.rawdata.startswith("<![CDATA[", i) and self._in_foreign():
                return super().parse_html_declaration(i)
            return self.parse_bogus_comment(i)
        return super().parse_html_declaration(i)

    def set_cdata_mode(self, elem, *args, **kwargs):
        # Foreign elements never enter raw-text mode; SVG <script> stays collected as today.
        if self._foreign_start and elem.lower() != "script":
            return
        return super().set_cdata_mode(elem, *args, **kwargs)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._in_foreign() and (
            tag in BREAKOUT_TAGS
            or (tag == "font" and any(n.lower() in ("color", "face", "size") for n, _ in attrs))
        ):
            while self._in_foreign():
                self._stack.pop()
        self._foreign_start = self._in_foreign() or (
            bool(self._stack)
            and self._stack[-1][1] == "math"
            and self._stack[-1][0] in MATH_TEXT_POINTS
            and tag in ("mglyph", "malignmark")
        )
        if self._foreign_start:
            ns = "svg" if tag == "svg" else self._stack[-1][1]
            if ns == "svg":
                point = tag in SVG_HTML_POINTS
            else:
                point = tag in MATH_TEXT_POINTS or (
                    tag == "annotation-xml"
                    and any(
                        n.lower() == "encoding"
                        and (v or "").strip().lower() in ("text/html", "application/xhtml+xml")
                        for n, v in attrs
                    )
                )
            self._stack.append((tag, ns, point))
        elif tag in ("svg", "math"):
            self._stack.append((tag, tag, False))
        if tag == "script" and not any(name.lower() == "src" for name, _ in attrs):
            self._chunks = []

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "script":
            self.handle_starttag(tag, attrs)
            self.set_cdata_mode(tag)
        else:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._chunks is not None:
            self._chunks.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._in_foreign() and tag in ("br", "p"):
            while self._in_foreign():
                self._stack.pop()
        else:
            for j in range(len(self._stack) - 1, -1, -1):
                if self._stack[j][0] == tag:
                    del self._stack[j:]
                    break
        if tag == "script" and self._chunks is not None:
            self.scripts.append("".join(self._chunks))
            self._chunks = None


def inline_scripts(text: str) -> list[str]:
    parser = InlineScripts()
    parser.feed(text)
    parser.close()
    return parser.scripts


def script_hash(body: str) -> str:
    return "sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()


def read_global_headers(path):
    """Header name (lowercase) -> value, for the block that starts with /*."""
    headers, active = {}, False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace():
            active = raw.strip() == "/*"
            continue
        if active and ":" in raw:
            name, value = raw.split(":", 1)
            headers[name.strip().lower()] = value.strip()
    return headers


def directive(csp, name):
    for part in csp.split(";"):
        bits = part.split()
        if bits and bits[0] == name:
            return bits[1:]
    return None


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    folder = Path(argv[1])
    headers_file = folder / "_headers"
    if not headers_file.is_file():
        print(f"FAIL: {headers_file} is missing")
        return 1
    headers = read_global_headers(headers_file)
    problems = [f"missing header: {name}" for name in REQUIRED if name not in headers]
    csp = headers.get("content-security-policy", "")
    script_src = directive(csp, "script-src") or directive(csp, "default-src") or []
    for bad in ("'unsafe-inline'", "'unsafe-eval'", "*", "https:", "http:", "data:"):
        if bad in script_src:
            problems.append(f"script-src allows {bad}")
    for need in ("object-src", "base-uri", "frame-ancestors"):
        if directive(csp, need) is None:
            problems.append(f"CSP has no {need}")
    allowed = {item.strip("'") for item in script_src if item.startswith("'sha256-")}

    seen = 0
    used = set()
    for page in sorted(folder.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for body in inline_scripts(text):
            seen += 1
            digest = script_hash(body)
            used.add(digest)
            if digest not in allowed:
                problems.append(f"{page.relative_to(folder)}: inline script not in the policy, add '{digest}'")
        if re.search(r"""\son(click|load|error|change|input|submit|focus|blur|key\w*|mouse\w*)\s*=""", text, re.I):
            problems.append(f"{page.relative_to(folder)}: has an inline event handler (on...=), which the policy blocks")
        if re.search(r"""(href|src)\s*=\s*["']\s*javascript:""", text, re.I):
            problems.append(f"{page.relative_to(folder)}: has a javascript: link, which the policy blocks")

    stale = allowed - used
    for item in sorted(stale):
        print(f"note: the policy lists a hash no page uses: '{item}'")

    if problems:
        print("FAIL:")
        for item in problems:
            print("  -", item)
        return 1
    print(f"ok: security headers are set; {seen} inline script(s) are covered by the policy ({folder})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
