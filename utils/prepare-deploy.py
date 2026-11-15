#!/usr/bin/env python3
"""Package checked Quarto output for Workers, without publishing source files."""

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"

# Preserve Quarto's .html URLs and the canonical homepage without SPA fallback.
(OUTPUT / "_redirects").write_text("/ /index.html 200\n")
(OUTPUT / "_headers").write_text(
    "/*\n  X-Content-Type-Options: nosniff\n"
    "  Referrer-Policy: strict-origin-when-cross-origin\n"
    "/release.json\n  Cache-Control: no-store\n"
)
(OUTPUT / ".assetsignore").write_text("wrangler.json\nCNAME\n.nojekyll\n")
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
files = {
    str(path.relative_to(OUTPUT)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(OUTPUT.rglob("*"))
    if path.is_file() and not any(part.startswith(".") for part in path.relative_to(OUTPUT).parts)
    and path.name not in {"release.json", "wrangler.json", "CNAME", "_redirects", "_headers"}
}
(OUTPUT / "release.json").write_text(json.dumps({"commit": sha, "files": files}, indent=2) + "\n")
print(f"Prepared {len(files)} assets for Workers; source commit {sha}.")
