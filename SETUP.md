# meding.dev — what we built

Personal card site for Michael Meding. Quiet luxury. Hosted on Cloudflare. Documented 14 August 2026.

Live: [https://meding.dev](https://meding.dev)  
Alias: [https://meding.pages.dev](https://meding.pages.dev)  
Repo: [https://github.com/mimeding/meding.dev](https://github.com/mimeding/meding.dev)  
Local: `/Users/mmeding/projects/meding.dev`

---

## Domain

| Field | Value |
|---|---|
| Domain | `meding.dev` |
| Registered | 13 August 2026 |
| Expires | 13 August 2029 (3 years prepaid) |
| Registrar | Cloudflare, Inc. (IANA 1910) |
| Account | Michael.e.meding@gmail.com's Account |
| Account ID | `6ac57ba3940abc23dade5daaf50ca161` |
| Nameservers | `adam.ns.cloudflare.com`, `meilani.ns.cloudflare.com` |
| DNSSEC | Off |
| TLD note | `.dev` is on the HSTS preload list. Browsers only load HTTPS. |

WHOIS is privacy-redacted through Cloudflare. Transfer lock (`client transfer prohibited`) is on. Leave it.

---

## Hosting

**Cloudflare Pages**, same account as the domain. No second host.

| Item | Value |
|---|---|
| Pages project | `meding` |
| Production branch | `main` |
| Publish directory | `public/` |
| Default hostname | `meding.pages.dev` |
| Custom hosts | `meding.dev`, `www.meding.dev` |

`www` 301s to the apex via `public/_redirects`.

### DNS that must exist

| Type | Name | Target | Proxy |
|---|---|---|---|
| CNAME | `@` | `meding.pages.dev` | Proxied |
| CNAME | `www` | `meding.pages.dev` | Proxied |

Cloudflare flattens the apex CNAME. Do not point these at a random IP. If you add only a CNAME and skip attaching the domain in Pages, you get a 522.

Dashboard:

- DNS: [records](https://dash.cloudflare.com/6ac57ba3940abc23dade5daaf50ca161/meding.dev/dns/records)
- Pages domains: [meding → Custom domains](https://dash.cloudflare.com/6ac57ba3940abc23dade5daaf50ca161/pages/view/meding/domains)

---

## Email

**Cloudflare Email Routing** is on and working.

| Public address | Forwards to |
|---|---|
| `michael@meding.dev` | `michael.e.meding@gmail.com` |

Routing **receives** only. Replies still go out from Gmail unless “Send mail as” is set up later.

Enable / edit: [Email Routing](https://dash.cloudflare.com/6ac57ba3940abc23dade5daaf50ca161/meding.dev/email/routing)

Cloudflare owns the MX and related TXT records. Do not delete them or mail stops.

---

## Git and deploy

- GitHub user: `mimeding`
- Repo: public, `mimeding/meding.dev`
- Push to `main` publishes, via `.github/workflows/deploy.yml` (`cloudflare/wrangler-action`)
- GitHub secrets on the repo:
  - `CLOUDFLARE_API_TOKEN`
  - `CLOUDFLARE_ACCOUNT_ID` = `6ac57ba3940abc23dade5daaf50ca161`

Manual deploy from the project root:

```bash
export CLOUDFLARE_API_TOKEN='…'
export CLOUDFLARE_ACCOUNT_ID='6ac57ba3940abc23dade5daaf50ca161'
npx wrangler@4 pages deploy public --project-name=meding --branch=main --commit-dirty=true
```

The first API token we used could create and deploy Pages but **could not read or write the DNS zone**. Custom-domain CNAMEs were added in the dashboard. For future API work on DNS or Email Routing, the token needs **Zone:Read** and **DNS:Edit** on `meding.dev`.

Do not commit tokens. Do not put the Global API Key in the repo.

---

## Site

One static page. No framework. No CMS. Paper-colored, serif name, black-and-white plates.

### Copy on the card (as of this note)

- **Name:** Michael Meding
- **Role:** Managing Director, McEwen Copper
- **Org:** President, Los Azules Copper Project
- **Lede (exact wording):** 25 years of international experience, 15 years in senior positions in mining. Building the global top 10 copper project Los Azules in Argentina.
- **Home:** San Juan & Toronto
- **Air:** Private pilot, SEL
- **Water:** PADI scuba instructor
- **AI:** Real-world business applications, local models, harness engineering and optimization.
- **Else:** Traveller. German, English, Spanish.
- **Contact:** michael@meding.dev · LinkedIn (`linkedin.com/in/michaelmeding`) · X (`@mmeding`)
- **Footer:** Mining Entrepreneur of the Year, Argentina · 2024 & 2025

### Photographs

Source files lived in `~/Downloads`. Web versions are warm monochrome JPEGs in `public/images/`.

| On the site | Source | What it is |
|---|---|---|
| `public/images/michael-meding.jpg` | `IMG_4644 2.jpg` | Headshot |
| `public/images/washington-2026.jpg` | `9b4b4820-ea79-4922-a559-b1845dd959af.JPG` | Washington, 2026. Benchmark Minerals. Presenting Los Azules. |
| `public/images/buenos-aires-nacion.jpg` | `e5c760a9-e34b-4c97-ac87-5afe1e79a91f.JPG` | Buenos Aires. La Nación interview. |

Captions:

- Washington, 2026. Benchmark Minerals. / Los Azules — and the case for investing in Argentine copper.
- Buenos Aires. La Nación. / On camera, on the country, and on the work in the Andes.

The CV (`Michael Meding CV June 2026.pdf`) was used to get facts. **It is not on the public site and not in the repo.** Phone number is not on the page.

### Design

- Background `#efe8db`, ink `#1c1814`, muted `#6d6559`, gold `#8d7349`
- Type: Cormorant Garamond + Outfit (Google Fonts)
- Light paper grain overlay
- `robots.txt` allows crawlers; sitemap points at `https://meding.dev/`
- No `noindex`. Search engines may fetch the page. They will not rank it until they discover it (Search Console / links).

---

## Layout of the repo

```
meding.dev/
  SETUP.md                 ← this file
  README.md
  .github/workflows/deploy.yml
  public/
    index.html             ← the whole site
    _headers
    _redirects
    favicon.svg
    robots.txt
    sitemap.xml
    images/
      michael-meding.jpg
      washington-2026.jpg
      buenos-aires-nacion.jpg
```

Only `public/` is published.

---

## What we deliberately left off

- Phone number
- Full CV / career dump
- Google Workspace (routing is enough for inbound)
- “Send mail as” from Gmail as `michael@meding.dev`
- DNSSEC
- Search Console submission

---

## How to change the page later

1. Edit `public/index.html` (or drop a new image in `public/images/`).
2. Commit and push to `main`, or run the `wrangler pages deploy` command above.
3. Hard-refresh [https://meding.dev](https://meding.dev).

New photos: resize to ~2000px on the long edge, same warm grayscale treatment as the existing plates, so they sit with the rest.
