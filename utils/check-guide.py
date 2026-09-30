#!/usr/bin/env python3
"""Check the guide's source links, navigation, and rendered discovery files."""

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
        self.heading = ""
        self.in_heading = False
        self.in_sidebar = False
        self.sidebar_links = []
        self.sidebar_link = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.metadata[attrs.get("name", attrs.get("property"))] = attrs.get("content", "")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1
            self.in_heading = True
        if tag == "nav" and attrs.get("id") == "quarto-sidebar":
            self.in_sidebar = True
        if tag == "a" and self.in_sidebar and "sidebar-link" in attrs.get("class", "").split():
            self.sidebar_link = {"href": attrs.get("href", ""), "text": "",
                                 "active": "active" in attrs.get("class", "").split()}
            self.sidebar_links.append(self.sidebar_link)
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
        if self.in_heading:
            self.heading += data
        if self.sidebar_link is not None:
            self.sidebar_link["text"] += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_heading = False
        if tag == "nav":
            self.in_sidebar = False
        if tag == "a":
            self.sidebar_link = None
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


def check_book_navigation(pages, texts):
    # Derive expectations from Quarto's chapter order and source headings.
    # Do not maintain a second navigation list alongside book.chapters.
    expected = {}
    for source, text in texts.items():
        heading = re.search(r"^# (.+?)(?:\s+\{[^}]+\})?$", text, re.M)
        expected[source.replace(".md", ".html")] = heading.group(1)

    def title(text):
        return re.sub(r"^\d+\s+", "", " ".join(text.split()))

    for name, page in pages.items():
        targets = [local_target(name, link["href"]) for link in page.sidebar_links]
        check(targets == [(target, "") for target in expected],
              f"{name}: sidebar chapter links/order differ from book.chapters")
        labels = [title(link["text"]) for link in page.sidebar_links]
        check(labels == list(expected.values()),
              f"{name}: sidebar titles differ from source headings")
        active = [local_target(name, link["href"]) for link in page.sidebar_links if link["active"]]
        check(active == [(name, "")], f"{name}: sidebar must highlight only the current chapter")
        check(title(page.heading) == expected[name], f"{name}: main heading differs from source")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rendered", action="store_true")
    args = parser.parse_args()
    chapters = re.findall(r"^\s+- (\S+\.md)$", (SECTIONS / "_quarto.yml").read_text(), re.M)
    texts = {name: (SECTIONS / name).read_text() for name in chapters}
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
    background = home.split("## Background & conceptualization")[-1]
    for url in ("https://www.amazon.com/dp/8269471100",
                "https://online.fliphtml5.com/loping/TheNorwegianMethodApplied/"):
        check(url in background, f"Missing Bakken book reference: {url}")
    ai_chapter = "section8_ai_assistance.md"
    ai_text = texts.get(ai_chapter, "")
    check(chapters[-1] == ai_chapter, "AI assistance must be the final chapter")
    check(ai_chapter in home, "Homepage missing the AI chapter link")
    check("{#plan-with-an-agent}" in ai_text and
          "Read https://norwegiansingles.run/llms-full.txt" in ai_text,
          "AI chapter missing the agent planning prompt")

    if args.rendered:
        dist = ROOT / "dist"
        files = {p.relative_to(dist).as_posix() for p in dist.rglob("*") if p.is_file()}
        pages = {name.replace(".md", ".html"): Page((dist / name.replace(".md", ".html")).read_text())
                 for name in chapters}
        check_rendered_links(files, pages, "HTML")
        check_book_navigation(pages, texts)
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
    print(f"Checked {len(chapters)} chapters and source links"
          + (", Quarto navigation, HTML/EPUB links, and SEO/LLM output." if args.rendered else "."))


if __name__ == "__main__":
    main()
