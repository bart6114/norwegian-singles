#!/usr/bin/env python3
"""Check the guide's published arithmetic and local source/rendered links."""

import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote, urlsplit
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "sections"
ERRORS = []


def check(condition, message):
    if not condition:
        ERRORS.append(message)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.duplicate_ids = set()
        self.links = []
        self.metadata = {}
        self.canonicals = []
        self.title = ""
        self.in_title = False
        self.in_json = False
        self.json_text = ""
        self.structured = []
        self.h1_count = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.metadata[attrs.get("name", attrs.get("property"))] = attrs.get("content", "")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_json = True
            self.json_text = ""
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.duplicate_ids.add(attrs["id"])
            self.ids.add(attrs["id"])
        if tag in ("a", "link") and "href" in attrs:
            self.links.append(attrs["href"])
        if tag in ("img", "script") and "src" in attrs:
            self.links.append(attrs["src"])

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_json:
            self.json_text += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_json:
            self.structured.append(json.loads(self.json_text))
            self.in_json = False


def local_target(origin, href):
    url = urlsplit(href)
    if url.scheme or url.netloc:
        return None
    path = unquote(url.path)
    if not path:
        target = origin
    elif path.startswith("/"):
        target = path.lstrip("/")
    else:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(origin), path))
    if target.endswith("/") or target in ("", "."):
        target = posixpath.join(target, "index.html")
    target = posixpath.normpath(target)
    return target, unquote(url.fragment)


def check_rendered_links(files, pages, label):
    for name, page in pages.items():
        check(not page.duplicate_ids, f"{label} {name}: duplicate anchors {page.duplicate_ids}")
        for href in page.links:
            url = urlsplit(href)
            if label == "HTML" and url.netloc == "norwegiansingles.run":
                href = url.path + ("#" + url.fragment if url.fragment else "")
            result = local_target(name, href)
            if result is None:
                continue
            target, fragment = result
            check(target in files, f"{label} {name}: missing {href}")
            if fragment and target in pages:
                check(fragment in pages[target].ids,
                      f"{label} {name}: missing anchor {href}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rendered", action="store_true")
    args = parser.parse_args()
    chapters = re.findall(r"^\s+- (\S+\.md)$", (SECTIONS / "_quarto.yml").read_text(), re.M)
    texts = {name: (SECTIONS / name).read_text() for name in chapters}
    implementation = texts["section2_implementing_the_method.md"]
    cards = {}
    pattern = re.compile(
        r"Time check: (\d+) \+ \((\d+) x (\d+)\) \+ \((\d+) x (\d+)\) "
        r"\+ (\d+) = (\d+) minutes running; (\d+) minutes quality\."
    )
    for letter in ("Intro", "A", "B", "C"):
        block = re.search(rf"^### {letter}:.*?(?=^### |^## |\Z)",
                          implementation, re.M | re.S)
        check(block is not None, f"Missing session {letter}")
        if block is None:
            continue
        matches = pattern.findall(block[0])
        variants = ("standard",) if letter == "Intro" else ("standard", "shorter", "larger")
        check(len(matches) == len(variants), f"Session {letter}: expected {len(variants)} time checks")
        for variant, match in zip(variants, matches):
            warm, reps, work, breaks, recovery, cool, total, quality = map(int, match)
            check(breaks == reps - 1, f"{letter} {variant}: recovery count")
            check(reps * work == quality, f"{letter} {variant}: quality total")
            check(warm + reps * work + breaks * recovery + cool == total,
                  f"{letter} {variant}: running total")
            cards[letter, variant] = total, quality
    check(len(pattern.findall(implementation)) == 10, "Expected ten session budgets")

    week_count = 0
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for name, text in texts.items():
        for block in re.findall(r"(?:^\|.*\|\s*\n)+", text, re.M):
            rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
                    for line in block.strip().splitlines()]
            if rows[0] != ["Day", "Session", "Running", "Quality"]:
                continue
            week_count += 1
            data = rows[2:-1]
            check([row[0] for row in data] == days, f"{name}: incomplete week")
            running = quality = 0
            for day, session, run, work in data:
                run, work = int(run), int(work)
                running += run
                quality += work
                check(0 <= work <= run, f"{name} {day}: invalid quality minutes")
                if session.startswith(("Intro:", "A:", "B:", "C:")):
                    variant = "larger" if "larger" in session else "shorter" if "shorter" in session else "standard"
                    check(cards.get((session.split(":", 1)[0], variant)) == (run, work),
                          f"{name} {day}: session differs from card {session}")
                else:
                    check(work == 0, f"{name} {day}: unexpected quality minutes")
            total = rows[-1]
            check(total[0] == "Total", f"{name}: missing total row")
            check((running, quality) == (int(total[2]), int(total[3])),
                  f"{name}: weekly sums do not match")
            hours, percentage = re.fullmatch(r"([\d.]+) hours; ([\d.]+)% quality", total[1]).groups()
            check(float(hours) * 60 == running, f"{name}: hours do not match")
            check(abs(float(percentage) - 100 * quality / running) <= 0.05,
                  f"{name}: quality percentage does not match")
    check(week_count == 6, "Expected six complete week tables")

    for name, text in texts.items():
        for href in re.findall(r"\]\(([^\s)]+)\)", text):
            result = local_target(name, href)
            if result is None:
                continue
            target, fragment = result
            check((SECTIONS / target).is_file(), f"{name}: missing source {href}")
            if fragment and target in texts:
                explicit = re.findall(r"\{#([^\s}]+)", texts[target])
                headings = re.findall(r"^#+ (.+)$", texts[target], re.M)
                implicit = {re.sub(r"[^\w\s-]", "", h).lower().replace(" ", "-") for h in headings}
                check(fragment in set(explicit) | implicit, f"{name}: missing source anchor {href}")
    home = texts["index.md"]
    check(home.count("https://mybook.to/XzwWbK3") == 1, "Homepage should have one book reference")
    check("https://mybook.to/XzwWbK3" in home.split("## Background & conceptualization")[-1],
          "Book reference must be in homepage background")
    check(not any(s in home for s in ("Get the Book", "<img", "linear-gradient", "onmouseover")),
          "Homepage still contains promotional book markup")
    check(len(re.findall(r"^## Progression", implementation, re.M)) == 1,
          "Keep a single progression section")

    if args.rendered:
        dist = ROOT / "dist"
        files = {p.relative_to(dist).as_posix() for p in dist.rglob("*") if p.is_file()}
        pages = {name.replace(".md", ".html"): Page((dist / name.replace(".md", ".html")).read_text())
                 for name in chapters}
        check_rendered_links(files, pages, "HTML")
        base = "https://norwegiansingles.run/"
        descriptions, titles, expected_urls = set(), set(), set()
        for name, page in pages.items():
            canonical = base + ("" if name == "index.html" else name)
            expected_urls.add(canonical)
            check(page.canonicals == [canonical], f"{name}: canonical URL")
            description = page.metadata.get("description", "")
            check(bool(description), f"{name}: missing description")
            check(description not in descriptions, f"{name}: duplicate description")
            descriptions.add(description)
            check(bool(page.title) and page.title not in titles, f"{name}: missing/duplicate title")
            titles.add(page.title)
            check(page.h1_count == 1, f"{name}: expected one main heading")
            check(page.metadata.get("og:description") == description, f"{name}: social description")
            check(page.metadata.get("og:url") == canonical, f"{name}: social URL")
            check(bool(page.metadata.get("twitter:card")), f"{name}: Twitter card")
            check("noindex" not in page.metadata.get("robots", ""), f"{name}: unexpectedly noindex")
            check(len(page.structured) == 1, f"{name}: structured data missing/duplicated")
            if page.structured:
                check(page.structured[0].get("url") == canonical, f"{name}: structured URL")
                check(page.structured[0].get("description") == description, f"{name}: structured description")
            markdown = name.replace(".html", ".llms.md")
            check(markdown in files, f"{name}: Markdown companion missing")
        sitemap = ET.parse(dist / "sitemap.xml")
        urls = {e.text for e in sitemap.findall(".//{*}loc")}
        download_urls = {base + p.name for suffix in ("pdf", "epub") for p in dist.glob(f"*.{suffix}")}
        check(expected_urls <= urls <= expected_urls | download_urls,
              "Sitemap must include canonical chapters and only existing downloads")
        robots = (dist / "robots.txt").read_text()
        check("Allow: /" in robots and f"Sitemap: {base}sitemap.xml" in robots, "robots.txt policy/sitemap")
        index = (dist / "llms.txt").read_text()
        full = (dist / "llms-full.txt").read_text()
        last_position = -1
        for name in chapters:
            companion = name.replace(".md", ".llms.md")
            check(base + companion in index, f"LLM index missing {companion}")
            markdown = (dist / companion).read_text().strip()
            position = full.find(markdown)
            check(position > last_position, f"Full guide missing/out of order: {companion}")
            last_position = position
            for href in re.findall(r"\]\(([^\s)]+)\)", markdown):
                result = local_target(companion, href)
                if result:
                    check(result[0] in files, f"{companion}: broken Markdown link {href}")
        check(base + "llms-full.txt" in index, "LLM index missing full guide")
        for suffix in ("pdf", "epub"):
            artifacts = list(dist.glob(f"*.{suffix}"))
            check(len(artifacts) == 1, f"Expected one rendered {suffix.upper()}")
        for path in dist.glob("*.epub"):
            with zipfile.ZipFile(path) as archive:
                check(archive.testzip() is None, "EPUB has a corrupt member")
                check(archive.read("mimetype") == b"application/epub+zip", "EPUB mimetype")
                members = set(archive.namelist())
                epub_pages = {name: Page(archive.read(name).decode()) for name in members
                              if name.endswith((".xhtml", ".html"))}
                check_rendered_links(members, epub_pages, "EPUB")
                check(any("nav" in p for p in epub_pages), "EPUB navigation missing")
    if ERRORS:
        raise SystemExit("\n".join(ERRORS))
    print(f"Checked {len(chapters)} chapters, {len(cards)} session budgets, {week_count} week tables"
          + (", HTML/EPUB links, and SEO/LLM output." if args.rendered else "."))


if __name__ == "__main__":
    main()
