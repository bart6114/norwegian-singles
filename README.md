<sub>This is the repository behind [norwegiansingles.run](https://norwegiansingles.run)</sub>

# Norwegian Singles Training Guide

This guide introduces the "Norwegian Singles" training approach, adapted from the high-volume Norwegian model often associated with double threshold sessions. This "singles" variant emphasizes frequent, *single* sub-threshold workouts per day, suitable for runners seeking sustainable improvement in aerobic capacity and performance over the long term, particularly those training 5-9 hours per week. The core idea is maximizing repeatable training load while managing fatigue.

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
* Install [quarto](https://quarto.org/docs/get-started/)
* Change dir to `/sections`
* Run `quarto preview`

## Acknowledgements

A big thanks goes to sirpoc (username `sirpoc84` on letsrun.com) for sharing his ideas, philosophy, and experiences. Major thanks also go to the other resources mentioned; I tried to list them all in the Background section of the [full summary](https://norwegiansingles.run).

The summarized knowledge is presented using [Quarto](https://quarto.org/) for a clean reading experience.
