# meding.dev

Personal site for [Michael Meding](https://meding.dev).

Static files in `public/` deploy to Cloudflare Pages. Push to `main` to publish.

How the domain, host, email, and page were set up: [SETUP.md](SETUP.md).

The approved September 2026 design uses `public/index.html` and `public/styles.css`, with a responsive introduction, contact links, selected appearances, and personal interests. It has no framework or JavaScript dependency.

`public/images/michael-meding-cutout.webp` is the approved edited portrait. Its CSS contour and lower fade blend it into the cream background; the image itself is not a transparent cutout. The original photograph remains available as `michael-meding.jpg`.

Preview locally with `python3 -m http.server 8000 --directory public`.
