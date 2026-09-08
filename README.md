# meding.dev

Personal site for [Michael Meding](https://meding.dev).

Static files in `public/` deploy to Cloudflare Pages. Push to `main` to publish.

How the domain, host, email, and page were set up: [SETUP.md](SETUP.md).

The approved September 2026 design uses `public/index.html` and `public/styles.css`, with a responsive introduction, contact links, selected appearances, and personal interests. It has no framework or JavaScript dependency.

`public/images/michael-meding-cutout.webp` is the approved edited portrait. Its CSS contour and lower fade blend it into the cream background; the image itself is not a transparent cutout. The original photograph remains available as `michael-meding.jpg`.

Preview locally with `python3 -m http.server 8000 --directory public`.

## Photo gallery

The September 2026 gallery adds nine supplied photographs under `public/images/`, with descriptive, URL-safe filenames. The original image bytes and aspect ratios are preserved. All gallery images load lazily and link to their full-size photograph; no JavaScript is required.

Appearances cover Benchmark GIGA USA 2026, LA NACION’s Minería interview with José Del Río, Latin America Day 2025, and two views of Nordic Funds & Mines. The Nordic photographs and LA NACION interview have no confirmed year in their supplied filenames, so their captions omit a year.

Recognition covers the personal Mining Entrepreneur of the Year award in 2025, McEwen Copper’s 2025 LIDE Argentina Premio INVERTIR in Mining, and two photographs of the 2023 Exploration Company of the Year award. Event descriptions follow the supplied filenames and visible event signage. The older Washington and Buenos Aires image assets remain available for existing links and social previews.
