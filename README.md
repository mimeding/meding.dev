# meding.dev

Personal site for [Michael Meding](https://meding.dev).

Static files in `public/` deploy to Cloudflare Pages. Push to `main` to publish.

How the domain, host, email, and page were set up: [SETUP.md](SETUP.md).

## Current site (27 September 2026)

Twenty static pages, generated from `site-src/`: profile, Los Azules, speaking and press, each in English (`/`), Spanish (`/es/`), German (`/de/`), Japanese (`/ja/`) and Simplified Chinese (`/zh/`). Every fact carries a numbered citation to the page where it was published.

- `site-src/content/<lang>.json`: all page text. English is the master; the other four follow `site-src/TRANSLATION_BRIEF.md`.
- `site-src/data/extracted.json`: speaking, press and quotes. `site-src/data/refs.json`: sources.
- `site-src/build.py`: writes the site. Rebuild with `cd site-src && MEDING_OUT=../public python3 build.py`, then push.
- `public/llms.txt` (short) and `public/llms-full.txt` (full text) for AI assistants; `public/facts.json` for structured data; `public/sitemap.xml` with language alternates; `public/robots.txt` allows search engines and AI crawlers.
- Fonts are self-hosted in `public/fonts/`. The pages load nothing from other hosts.
- `DEPLOY.md`: Cloudflare settings and the steps after each upload.

`public/images/` holds the photographs of the previous site. They stay published so existing links keep working.

## Previous sites

The single-page reference entry, live until 27 September 2026, is on branch `archive/open-record-2026-09-27`.


The personal card with the photo gallery, as live until 26 September 2026, is kept on branch `archive/personal-card-2026-09`. To restore it, check out `public/` from that branch and push to `main`.

Preview locally with `python3 -m http.server 8000 --directory public`.
