# Security

This is a personal portfolio project, shown as a proof of concept. If you find something that could be abused, please report it privately and not in a public issue.

Open the **Security** tab of this repo and choose **Report a vulnerability**. Include the page or file, what you did and what happened.

## What protects the site

- A strict Content-Security-Policy and other security headers, set in `site/_headers`. A check in CI fails if the policy is loosened.
- Pages are static files on Cloudflare. There is no database, no login and no server code to attack.
- Every push is scanned for committed secrets (gitleaks) and for code problems (CodeQL). Dependabot keeps the build tools current.
