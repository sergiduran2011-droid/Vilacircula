# VilaCircula standalone website

This folder is the independent, static marketing website. It does not depend on the VilaCircula app or API.

To publish it on another static host, copy **all files in this folder** while keeping them together, then set `index.html` as the site's entry page. No build step is required.

- `index.html`: page content and SEO metadata
- `style.css`: responsive layout and visual design
- `script.js`: language selector, mobile menu, animations, and sharing
- `legal.html`: the website's standalone legal information
- `favicon.svg`: site icon

Google Fonts and AOS load from CDNs; the page layout and its scroll-animation fallback still work if those services are unavailable.
