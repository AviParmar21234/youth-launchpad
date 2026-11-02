# Youth LaunchPad — Brand Kit

The visual identity for youthlaunchpad.org, derived from the Foundation's logo
(a gold deck over a green bridge, a road running beneath it, three figures with
arms raised on top). Everything on the site comes from that mark.

## 1. Palette

| Name | Hex | Use it for |
|---|---|---|
| Forest | `#163A2B` | Headlines, body text, primary buttons, dark sections. Sampled from the logo's green. |
| Forest Deep | `#0E2A1F` | Footer only. |
| Pine | `#1F5240` | Hover state for Forest buttons, link color on light surfaces. |
| Gold | `#BD9548` | Accents: the bridge deck, underlines, step rules, gold buttons. Sampled from the logo's gold. |
| Gold Deep | `#9A7832` | Gold used as *text* on light backgrounds (meets contrast). The "Youth" in the wordmark. |
| Gold Pale | `#F1E7CC` | The call-to-action band, icon circles, "Planned" status pills. |
| Mist | `#F3F6F2` | Page background. A cool green-white, deliberately not cream. |
| Sage Light | `#E9EFE8` | Topic pills, founder frame, success messages. |
| White | `#FFFFFF` | Alternating sections, panels, form fields. |
| Text Soft | `#4B5F54` | Secondary copy and ledes. |

**Rules**
- Backgrounds alternate Mist and White. Forest is used for one full-bleed section per page at most.
- Gold is an accent, never a surface for body text. On light backgrounds, gold text is always Gold Deep.
- Never use pure black or a near-black. Forest is the darkest color on the site.

## 2. Typography

| Typeface | Job | How |
|---|---|---|
| **Bricolage Grotesque** (600–700) | Headlines, pull quotes, nav wordmark, form legends | Tight tracking (`-0.02em` to `-0.03em`), line-height near 1.0 for the largest sizes. |
| **Albert Sans** (400–600) | Body, UI, buttons, labels | Regular for paragraphs, 600 for buttons and labels. Sentence case everywhere; no tracked-out capitals. |

Both load from Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Albert+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet" />
```

Type scale (CSS classes in `site/css/styles.css`): `.h1` 44–86px, `.h2` 32–50px, `.h3` 22–26px, `.lede` 18–21px, body 17px.

## 3. The arch

The one signature shape. It appears as:
- the **hero bridge**: gold deck arc, green inner arch, piers, and the road, drawn once on page load;
- **arch-topped panels** (`.arch`) for the three programs, `border-radius: 999px 999px 14px 14px`;
- the **founder frame** (`.founder__mark`), ready to hold a headshot;
- a faint **arc ornament** behind each inner page title.

Do not add rounded cards, gradients, or drop shadows elsewhere. Rows divided by hairlines (`.ways`, `.places`, `.outline`) carry lists; arches carry the programs.

## 4. Logo

- `site/images/logo-full.png` — full lockup, transparent, for light backgrounds.
- `site/images/logo-full-light.png` — white and gold version for the Forest footer.
- `site/images/emblem.png` — the bridge mark alone, used in the nav at 46px tall and as the favicon source.
- Minimum height for the emblem: 32px. Keep clear space of at least the height of the figures around it.
- Do not recolor the gold or place the dark lockup on Forest.

## 5. Voice

Plain, warm, and honest about where the Foundation is. Say "developing" and "planned" when that is true. Active verbs on buttons ("Request a workshop", not "Submit"). No exclamation marks. Never invent statistics, testimonials, or partner names.
