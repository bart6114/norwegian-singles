#!/usr/bin/env python3
"""Complete static discovery metadata after Quarto renders HTML."""

from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ROOT / "sections"
CONFIG = (SECTIONS / "_quarto.yml").read_text()
BASE = re.search(r"^\s+site-url: (\S+)$", CONFIG, re.M)[1].rstrip("/")
CHAPTERS = re.findall(r"^\s+- (\S+\.md)$", CONFIG, re.M)
OUTPUT = (SECTIONS / os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", "../dist")).resolve()
BLOCK = re.compile(r"\n<!-- guide-discovery:start -->.*?<!-- guide-discovery:end -->\n", re.S)


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.description = ""
        self.title = ""
        self.in_title = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name") == "description":
            self.description = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def main():
    rendered = os.environ.get("QUARTO_PROJECT_OUTPUT_FILES", "")
    if rendered and not any(line.endswith(".html") for line in rendered.splitlines()):
        return
    full = ["# Norwegian Singles", "", "The complete guide, in reading order. "
            "Worked schedules are editorial examples; source references and qualifications remain part of the text.", ""]
    complete = True
    entries = []
    for chapter in CHAPTERS:
        name = Path(chapter).stem
        path = OUTPUT / (name + ".html")
        markdown = OUTPUT / (name + ".llms.md")
        if not path.exists():
            complete = False
            continue
        text = BLOCK.sub("", path.read_text())
        if name == "index":
            # The book landing page otherwise has both a book H1 and a chapter H1.
            text = re.sub(r'<header id="title-block-header"[^>]*>.*?</header>', "", text, flags=re.S)
        meta = Metadata(text)
        canonical = BASE + "/" + ("" if name == "index" else name + ".html")
        # Use one canonical URL, including when a future Quarto version emits it.
        text = re.sub(r'<link\b(?=[^>]*\brel=[\"\']canonical[\"\'])[^>]*>\s*', "", text)
        # The book's social defaults can override a chapter's description.
        text = re.sub(r'<meta\b(?=[^>]*(?:name|property)=[\"\'](?:og:description|twitter:description|og:url)[\"\'])[^>]*>\s*', "", text)
        data = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": meta.title,
            "description": meta.description,
            "inLanguage": "en",
            "isPartOf": {
                "@type": "WebSite", "@id": BASE + "/#website",
                "url": BASE + "/", "name": "Norwegian Singles",
            },
        }
        encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
        head = (f'\n<!-- guide-discovery:start -->\n'
                f'<link rel="canonical" href="{escape(canonical, quote=True)}">\n'
                f'<meta property="og:url" content="{escape(canonical, quote=True)}">\n'
                f'<meta property="og:description" content="{escape(meta.description, quote=True)}">\n'
                f'<meta name="twitter:description" content="{escape(meta.description, quote=True)}">\n'
                f'<link rel="alternate" type="text/markdown" href="{BASE}/{name}.llms.md" title="Markdown version">\n'
                f'<link rel="alternate" type="text/plain" href="{BASE}/llms.txt" title="Guide index for AI tools">\n'
                f'<script type="application/ld+json">{encoded}</script>\n'
                '<!-- guide-discovery:end -->\n')
        text = text.replace("</head>", head + "</head>", 1)
        # Align homepage social URLs with its canonical URL.
        if name == "index":
            text = text.replace(f'content="{BASE}/index.html"', f'content="{BASE}/"')
        path.write_text(text)
        if markdown.exists():
            content = markdown.read_text()
            # Custom Quarto anchors do not survive its plain-Markdown conversion.
            # Point section links at the HTML anchor instead of a nonexistent Markdown anchor.
            def section_link(match):
                href = match[1]
                url = urlsplit(href)
                if not url.scheme and not url.netloc and url.fragment:
                    target = url.path.replace(".llms.md", ".html") if url.path else name + ".html"
                    return "](" + BASE + "/" + target + "#" + url.fragment + ")"
                return match[0]
            content = re.sub(r"\]\(([^\s)]+)\)", section_link, content)
            markdown.write_text(content)
            full.extend(["---", "", f"Source: {canonical}", "", content.strip(), ""])
            source = (SECTIONS / chapter).read_text()
            heading = re.search(r"^# (.+?)(?:\s+\{[^}]+\})?$", source, re.M)[1]
            entries.append(f"- [{heading}]({BASE}/{name}.llms.md): {meta.description}")
        else:
            complete = False

    # Avoid publishing a partial full-guide file during a fresh single-page preview.
    if complete:
        (OUTPUT / "llms-full.txt").write_text("\n".join(full))
        index = OUTPUT / "llms.txt"
        # Native book titles contain Pandoc span syntax; use the source headings.
        description = re.search(r'^  description: "(.+)"$', CONFIG, re.M)[1]
        index.write_text("# Norwegian Singles\n\n> " + description + "\n\n## Pages\n\n"
                         + "\n".join(entries)
                         + f"\n\n## Complete guide\n\n- [Full guide]({BASE}/llms-full.txt): All chapters in reading order.\n")

    # Quarto owns the sitemap. Keep its homepage consistent with the canonical URL.
    sitemap = OUTPUT / "sitemap.xml"
    if sitemap.exists():
        sitemap.write_text(sitemap.read_text().replace(f"<loc>{BASE}/index.html</loc>", f"<loc>{BASE}/</loc>"))
    (OUTPUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    print("Updated canonical URLs, structured data, robots.txt, and full-guide text.")


if __name__ == "__main__":
    main()
