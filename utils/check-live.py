#!/usr/bin/env python3
"""Verify a complete Workers release over HTTPS, not just a successful build."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="https://norwegiansingles.run")
parser.add_argument("--manifest", type=Path, help="Compare against the local release manifest")
parser.add_argument("--wait", type=int, default=0, help="Seconds to wait for the expected release")
args = parser.parse_args()
base = args.url.rstrip("/")
if not base.startswith("https://"):
    parser.error("Live checks require HTTPS with normal certificate validation")
expected = json.loads(args.manifest.read_text()) if args.manifest else None


def fetch(path):
    url = base + "/" + path
    with urlopen(Request(url, headers={"User-Agent": "NorwegianSingles-ReleaseCheck/1.0"}), timeout=30) as response:
        if response.status != 200 or response.url != url:
            raise ValueError(f"Unexpected status or redirect: {path} -> {response.url}")
        return response.read()


deadline = time.monotonic() + args.wait
while True:
    try:
        live = json.loads(fetch("release.json"))
        if expected is not None and live != expected:
            raise ValueError(f"Waiting for {expected['commit']}; live is {live.get('commit')}")
        break
    except (HTTPError, URLError, ValueError) as error:
        if time.monotonic() >= deadline:
            raise SystemExit(f"Release check failed: {error}")
        print(str(error), flush=True)
        time.sleep(15)

files = live["files"]
required = {"index.html", "search.json", "Norwegian-Singles.pdf", "Norwegian-Singles.epub",
            "robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"}
if not required <= files.keys() or len([p for p in files if p.endswith(".html")]) != 9:
    raise SystemExit("Release manifest is missing guide assets")


def check(item):
    path, digest = item
    if hashlib.sha256(fetch(path)).hexdigest() != digest:
        raise ValueError(f"Published bytes differ: {path}")


with ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(check, files.items()))
check(("", files["index.html"]))
for path in ("this-page-must-not-exist", "wrangler.json", "CNAME", ".assetsignore"):
    try:
        fetch(path)
    except HTTPError as error:
        if error.code == 404:
            continue
        raise
    raise SystemExit(f"Expected 404 for {path}")
print(f"Verified {len(files)} assets, homepage, HTTPS and 404s at {base}; commit {live['commit']}.")
