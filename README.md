# meding.dev

Personal site for [Michael Meding](https://meding.dev).

Static files in `public/` deploy to Cloudflare Pages. Push to `main` to publish.

How the domain, host, email, and page were set up: [SETUP.md](SETUP.md).

## Current site: Open Record (September 2026)

A reference entry on Michael Meding, the Los Azules copper project and McEwen Copper. Every fact carries a numbered citation to the page where it was published.

- `public/index.html`: English page. `public/es/index.html`: Spanish page. Both carry both languages and switch in place.
- `public/img/`: photographs used by the page, plus `og.jpg` (1200 × 630 share image).
- `public/llms.txt`: plain-language summary with a source link on every line, for AI assistants.
- `public/facts.json`: the same facts in English and Spanish as structured data.
- `public/robots.txt`: allows search engines and AI crawlers. `public/sitemap.xml`: both language pages plus the two files above.
- The schema.org JSON-LD graph (Person, Organization, Place, FAQPage, events) is inside each page.

The page has no build step on the host. Fonts come from Google Fonts; there is no other external dependency.

`public/images/` holds the photographs of the previous site. They stay published so existing links and social previews keep working.

## Previous site

The personal card with the photo gallery, as live until 26 September 2026, is kept at tag `archive-2026-09-26-personal-card` and branch `archive/personal-card-2026-09`. To restore it, check out `public/` from that tag and push to `main`.

Preview locally with `python3 -m http.server 8000 --directory public`.
