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
from pathlib import Path

REQUIRED = ["content-security-policy", "x-content-type-options", "referrer-policy", "x-frame-options", "permissions-policy"]


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
    for page in sorted(folder.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for match in re.finditer(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", text, re.S | re.I):
            if re.search(r"\bsrc\s*=", match.group("attrs")):
                continue
            seen += 1
            digest = "sha256-" + base64.b64encode(hashlib.sha256(match.group("body").encode("utf-8")).digest()).decode()
            if digest not in allowed:
                problems.append(f"{page.relative_to(folder)}: inline script not in the policy, add '{digest}'")
        if re.search(r"""\son(click|load|error|change|input|submit|focus|blur|key\w*|mouse\w*)\s*=""", text, re.I):
            problems.append(f"{page.relative_to(folder)}: has an inline event handler (on...=), which the policy blocks")
        if re.search(r"""(href|src)\s*=\s*["']\s*javascript:""", text, re.I):
            problems.append(f"{page.relative_to(folder)}: has a javascript: link, which the policy blocks")

    stale = allowed - {
        "sha256-" + base64.b64encode(hashlib.sha256(m.group("body").encode("utf-8")).digest()).decode()
        for page in folder.rglob("*.html")
        for m in re.finditer(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", page.read_text(encoding="utf-8"), re.S | re.I)
        if not re.search(r"\bsrc\s*=", m.group("attrs"))
    }
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
