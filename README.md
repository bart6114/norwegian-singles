<sub>This is the repository behind [norwegiansingles.run](https://norwegiansingles.run)</sub>

# Norwegian Singles Training Guide

This guide explains the Norwegian Singles running routine: three controlled sub-threshold sessions each week, with easy running between them and an easy longer run. It includes a 30-minute introductory workout, examples for three or more running days, and guidance for progression, recovery, and racing. Start with the running you already sustain and use the examples to plan a repeatable week.

## Project Background & Motivation

I first heard about the "Norwegian Singles" training method somewhere on Reddit. When I started looking into it, I initially only found the massive Letsrun thread, which was far too much information to digest effectively.

To get a clearer picture, I decided to scrape all messages in this thread (aka a sh*tton of messsages). You can find the source documents in `data/results.json` and the scraping utility functions in `/utils`.

I then used `google/gemini-2.5-pro-preview-03-25` in `cline` to summarize the key findings from these scraped documents. Along the way, I discovered several other valuable resources, which have been compiled in the Background section of the summary.

The full summary is available in web, pdf and epub format on [norwegiansingles.run](https://norwegiansingles.run).

The prompt used in `cline` to construct `/intermediary/BOOK.md` quoted below, this was repeated until all `/data/results-lite-*.json` were processed.

> Please continue reading the results files one by one. Start by the last one quoted in BOOK.md if it exists. Read in the next 10 files in the /results for ascendingly. After reading 10 files, create/update the BOOK.md to incorporate relevant content, rearranging or changing headers and structure as needed to best fit the new information. This is supposed to be a short but concise (<1000 lines) introduction to what norwegian singles are and how to build a workout plan accordingly. On the final line of BOOK.md keep a reference to the last file processed. After processing 10 files and updating the book: STOP.

The `BOOK.md` file was separated into the sections in `/sections` again via the aforementioned model. Some manual fine tuning was done on the final document and some extra resources added where I deemed it relevant.

## Open Repository & Disclaimer

This is an open repository. All contributions are very welcome and encouraged. The easiest way is just to create a PR to contribute your changes.

Please note that this is by no means meant as an authoritative resource on the Norwegian Singles training method. It's primarily a way to gather and spread the knowledge that's currently scattered across various online sources.

If anyone is genuinely interested in building this project out further, please message me. I'm also open to transferring the domain name (if applicable) to someone who really wants to give this shape. My only goal here is to share the information compiled here.

## Running Locally

* Clone this repository
* Install [Quarto 1.10.18 or newer](https://quarto.org/docs/get-started/). The publishing workflow pins 1.10.18, the latest stable release checked on 18 September 2026.
* Change dir to `/sections`
* Run `quarto preview`

## Editing the guide

The reading route explains effort first, then shows how to adapt an existing week, follow a complete workout, and adjust for recovery or races. Tools, load metrics, comparisons, and sources follow as optional reading. The existing chapter filenames are kept so published page URLs continue to work.

Keep navigation in Quarto: `book.chapters` in `sections/_quarto.yml` sets the order, and each chapter's first heading supplies its sidebar label. Use source `.md` links with heading anchors for links between chapters; Quarto resolves them for each output format. Do not maintain separate HTML sidebars or hard-code chapter numbers in link text. If a newly deployed homepage leads to an older-looking chapter, reload that chapter: GitHub Pages currently serves HTML with a ten-minute cache lifetime.

Edit the Markdown in `sections/`. Week tables and session cards live in the implementation chapter; link to them instead of copying their numbers into other chapters. The historical scrape and `intermediary/BOOK.md` are source archives, not the current published guide. Quarto builds HTML, PDF, and EPUB from the same chapter files into the ignored `dist/` directory. The PDF-only filter in `utils/guide-pdf-layout.lua` reserves space for schedules and workout instructions so they stay together; check it when changing those blocks.

For each content change:

* Identify the reader's question and give an action they can take. Keep the reader's existing days, rest days, and running time as the starting point. Explain terms before using them in instructions; label calendars as examples and keep session cards independent of weekdays.
* Cite original descriptions for specific prescriptions. Label editorial examples and distinguish adaptations from the standard method. Do not turn a secondhand book quotation into an official rule without checking the passage and edition.
* Check running minutes, quality minutes, and elapsed time separately. Recovery occurs between repetitions, not after the final repetition. Recalculate the whole week when changing a session.
* Keep the tone plain and practical. Apply the Humanizer editorial process: flag formulaic writing, rewrite it, then check that no facts, numbers, qualifications, or citations changed unintentionally. Keep promotional language out of the guide; the homepage book reference belongs in its background section.
* Check related chapters for contradictions. Keep one progression section and link to it from other pages.

From the repository root, run:

```sh
python3 utils/check-guide.py
quarto render sections --to all
python3 utils/check-guide.py --rendered
```

The checker validates session arithmetic, weekly totals, links between source chapters, and rendered HTML/EPUB links. It also checks every page's sidebar order, labels, active chapter, and main heading against the Quarto chapter sources. Also inspect the website at desktop and phone widths, PDF tables and page breaks, and EPUB navigation. PDF rendering needs a LaTeX installation; the publishing workflow installs TinyTeX.

Keep the three editorial releases reviewable: starting weeks and session instructions; progression, recovery, and racing; then tools and background. Review all formats before merging to `main`, since a push there triggers the existing GitHub Pages publishing workflow. Generated files in `dist/` should not be committed.

## Search and AI-readable output

Quarto 1.10.18 has [native `llms.txt` support](https://quarto.org/docs/websites/website-llms.html), including a Markdown companion for each HTML page. No third-party extension is needed. The post-render script combines those companions into `llms-full.txt` in book order, adds canonical links and WebPage/WebSite structured data, and keeps the sitemap homepage URL consistent. All of these files are regenerated from the guide.

Each chapter has a distinct page title and description. Quarto supplies social previews and a sitemap; the post-render script supplies an explicit crawl policy and links to the Markdown alternatives. The footer records the editorial update date; change it when revising the published content. Keep structured data consistent with the visible text, without inventing reviews, credentials, or claims about results.

The `--rendered` check covers these discovery files as well as book links. After deployment, check the public homepage, sitemap, `robots.txt`, `llms.txt`, and `llms-full.txt`. Search Console submission and traffic monitoring happen separately from the local build. AI-readable files help tools consume the guide; they do not guarantee search rankings or AI citations. [Google's guidance](https://developers.google.com/search/docs/appearance/ai-features) applies the same search fundamentals to its AI features.

## Acknowledgements

A big thanks goes to sirpoc (username `sirpoc84` on letsrun.com) for sharing his ideas, philosophy, and experiences. Major thanks also go to the other resources mentioned; I tried to list them all in the Background section of the [full summary](https://norwegiansingles.run).

The summarized knowledge is presented using [Quarto](https://quarto.org/) for a clean reading experience.
