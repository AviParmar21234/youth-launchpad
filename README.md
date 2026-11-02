# Youth LaunchPad — Website

Static site for **The Youth LaunchPad Foundation, Inc.** (youthlaunchpad.org).
Built from the client brief in `source/` (ten Word documents and the logo).

```
site/            ← the deployable website (upload this folder as-is)
  index.html, about.html, programs.html, students.html, partners.html,
  get-involved.html, resources.html, faq.html, contact.html,
  privacy.html, terms.html, accessibility.html
  css/styles.css   js/main.js   images/
tools/           ← page sources and the build script
  layout.html    shared header, nav, footer, meta
  pages/*.html   one body per page, with a title/description front-matter block
  build.py       assembles tools/pages + layout → site/*.html
source/          ← the client's original brief (unzipped from websiteinfo.zip)
BRAND.md         ← palette, type, logo rules
```

## Preview locally

```bash
python3 -m http.server 8765 --directory site
```

Then open http://localhost:8765. (Opening the HTML files directly also works; only the forms behave differently without a server.)

## Live site

Hosted on Vercel as project `youth-launchpad` (public address: https://youth-launchpad.vercel.app). `vercel.json` serves the `site/` folder with clean URLs (`/about` instead of `/about.html`).

To publish changes after rebuilding:

```bash
vercel deploy --prod --yes
```

Preview deployments (`vercel deploy`) are protected by a Vercel login by default; use the production address when sharing with the client. When youthlaunchpad.org is ready, add it as a domain to the project in the Vercel dashboard.

## Editing content

1. Edit the page body in `tools/pages/<page>.html`. Header, footer, and nav live once in `tools/layout.html`.
2. Rebuild:

```bash
python3 tools/build.py
```

3. Upload the `site/` folder.

If a non-technical editor needs to change text without running the build, they can edit `site/*.html` directly; just know the next `build.py` run will overwrite those edits, so copy the change into `tools/pages/` too.

## Forms

Five inquiries share one component: Request a workshop, Become a partner, Volunteer or mentor, Corporate sponsorship (all on Get involved), and Contact.

- Right now `data-endpoint=""` on each `<form>`, so submitting opens the visitor's email app with the message pre-filled and addressed to info@youthlaunchpad.org. Nothing is stored anywhere.
- To receive submissions in an inbox or dashboard, create a form endpoint (Formspree, Basin, Netlify Forms, or similar), then set `data-endpoint="https://..."` on the two forms in `tools/pages/get-involved.html` and `tools/pages/contact.html` and rebuild. `js/main.js` posts JSON to it and shows a confirmation.
- A honeypot field (`website_url`) drops obvious bots. Add the provider's spam protection on top.

## Before launch — approvals checklist

From the brief's launch controls. Nothing below should go live unverified.

- [ ] Founder title "Founder & Executive Director" confirmed (About, Home).
- [ ] Founder bio approved; headshot supplied (drop into `.founder__mark` on About and Home, replacing the emblem).
- [ ] Partner names on Schools & partners ("Working with" strip): Miami Dade College and Booker T. Washington Senior High School. Confirm both relationships and the exact names before publishing.
- [ ] Board of directors: not yet on the site. Add a Leadership block on About once names, titles, and photos are approved.
- [ ] 501(c)(3) status: the site currently says tax-exempt status is pending and that donations are not accepted. Update FAQ, Terms, and the footer line when the determination letter arrives.
- [ ] Florida charitable-solicitation registration (or exemption) before any donate button is added.
- [ ] Privacy, Terms, and Accessibility pages reviewed by counsel; they are drafts.
- [ ] Program names and descriptions approved; curriculum outlines confirmed as available on request (Resources).
- [ ] Social links: none are on the site yet. Add to the footer once LinkedIn/Instagram/Facebook/YouTube URLs exist.
- [ ] Photography: the site is designed to work without photos. When approved, consented images are available, the `.arch` panels and `.founder__mark` accept them. No stock photos presented as program photos.
- [ ] Confirm `info@youthlaunchpad.org` is live and monitored.
- [ ] Domain DNS pointed at the host; `https://youthlaunchpad.org/` canonical URLs are already in every page.

## Pages the brief listed that are not built yet

**Impact** and **Events & Updates** were left out on purpose: there are no results or events to publish, and an empty page costs credibility. Add them as program delivery begins. The site structure supports it (copy any `tools/pages/*.html` as a starting point).

## Quality floor

- Mobile-responsive down to 320px; mobile menu under 1060px.
- Keyboard navigable with visible focus, skip link, semantic landmarks, labelled forms.
- `prefers-reduced-motion` disables the hero animation.
- Open Graph image, meta descriptions, canonical URLs, and `schema.org/NGO` structured data on every page.
- No third-party scripts. Fonts are the only external request.
