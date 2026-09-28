# meding.dev: deploy

Nothing here is live yet. Upload only after Michael has approved the preview and McEwen's qualified person and disclosure committee have signed off the Los Azules page.

## Upload
Replace the `public/` folder in the GitHub repo `mimeding/meding.dev` with the `public/` folder from this package, commit and push to `main`. The existing workflow (`.github/workflows/deploy.yml`) publishes it to Cloudflare Pages.

Manual alternative from the repo root:
`npx wrangler@4 pages deploy public --project-name=meding --branch=main`

## What is in public/
- 20 pages: profile, Los Azules, speaking and press, each in English (/), Spanish (/es/), German (/de/), Japanese (/ja/) and Simplified Chinese (/zh/). Each page is one language only, with its own title, description, canonical URL, hreflang links and schema.org JSON-LD.
- `404.html`: a real 404 page. Without it Cloudflare Pages returns the home page with status 200 for any unknown address.
- `sitemap.xml` (20 pages with language alternates and images), `robots.txt` (all search engines and AI crawlers allowed), `llms.txt` (short summary), `llms-full.txt` (full English text with sources), `facts.json` (structured facts).
- `fonts/`: the three Latin typefaces, self-hosted. Japanese and Chinese pages use the reader's system fonts. No request goes to Google Fonts.
- `_headers`: security and cache headers; `noindex` on `*.pages.dev` preview addresses and on the legacy `/images/` folder. `_redirects`: /en, /jp, /zh-hans and /zh-cn to the right language.
- `img/og-<lang>.jpg`: share image per language. `img/michael-meding-headshot.jpg`: square headshot for the structured data and press kit (replace with a colour headshot of at least 1200 px when available).
- `images/`: photos of the previous site, kept so old links keep working.

## Cloudflare settings (dashboard)
1. The www redirect is handled in the repo by `functions/_middleware.js` (301 from www.meding.dev to meding.dev). No dashboard rule is needed.
2. Security > Bots: Bot Fight Mode off; "Block AI bots" off.
3. Overview or AI Crawl Control: "Manage robots.txt" (Cloudflare's managed robots.txt) off, so the site's own robots.txt is served.
4. Caching > Configuration: Crawler Hints on (sends IndexNow pings to Bing, Yandex and others).

## IndexNow
The key file `91a11054d3a9439d5822987f0985c101.txt` sits in `public/` (source: `site-src/assets/`). After a content change, ping `https://api.indexnow.org/indexnow?url=<page URL>&key=91a11054d3a9439d5822987f0985c101` for each changed page, or rely on Cloudflare Crawler Hints once it is on.

## After upload
1. Google Search Console: add the domain property meding.dev, submit https://meding.dev/sitemap.xml, request indexing for / and /los-azules/.
2. Bing Webmaster Tools: import from Search Console, submit the sitemap.
3. Put https://meding.dev in the website field of LinkedIn and X, and in speaker bios.

## Editing later
All text lives in `site-src/content/<lang>.json` (English is the master). Speaking, press and quotes are in `site-src/data/extracted.json`; sources in `site-src/data/refs.json`. Rebuild with:
`cd site-src && MEDING_OUT=../public python3 build.py`
New English text needs the same change in the other four language files; `TRANSLATION_BRIEF.md` has the rules the translations follow.
