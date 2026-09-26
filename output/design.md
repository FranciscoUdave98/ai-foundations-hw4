# Design (Problem 10)

What changed, and why it helps shoppers stay longer and buy.

## Changes

| Change | Where | Why it helps |
|---|---|---|
| **Yale navy (#00356B) and white only.** All other blues became navy tints; the page background is white. | `index.css` palette | Looks like official Yale gear at first glance, which builds trust. Navy buttons stand out against white, so "Shop the collection", "Ask the Bulldog", and "Add to bag" are easy to find. |
| **Handsome Dan and Yale art**: a bulldog face (nav badge, favicon, chat avatar, launcher), a full Dan with a "Y" collar (hero, banners, About, 404), a "Y · 1701" shield, a "YALE UNIVERSITY" wordmark, and paw prints. | `components/Brand.tsx`, `index.html` | A mascot gives the shop a personality students recognize and share. The 404 page ("Ruff! Handsome Dan chased this page off campus") turns a dead end into a smile and a "Back home" button. |
| **Fun type**: *Graduate* (varsity lettering) for headlines, prices, category pills, and the ribbon; *Fraunces* (soft, playful serif) for headings. Both are bundled with the site, so there are no external requests. | `main.tsx`, `index.css` | Varsity lettering matches the merch itself, and prices in bold type are easy to scan when comparing. |
| **Page-load motion**: a Dan splash while the app starts, a navy progress bar with trotting paw prints on every page change, pages sliding in, headlines "stamping" in, and product cards appearing one after another. | `index.html`, `App.tsx`, `index.css` | Shows something is happening right away, so waits feel shorter and fewer people leave. The staggered cards draw the eye across more products. |
| **Movement that invites clicks**: a scrolling "Go Bulldogs · Boola Boola · Since 1975" ribbon, Dan bouncing in the hero, icons tilting on hover. | Home | Gives returning visitors something to notice and keeps attention on the page. |
| **"Bulldog Assistant"**: the chat is renamed, with a Dan avatar next to every reply and an "Ask the Bulldog" launcher. A new hero button opens the chat directly. | `ChatWidget.tsx`, prompt | A named character is more approachable than "chat". An obvious way to ask "is this in M?" helps shoppers get to the purchase. |
| **Fun waiting state**: instead of three dots, Dan bobs, flaps his ears, and sniffs, with walking paw prints next to the live status line ("Hunting for Larges…"). | `ChatWidget.tsx`, `index.css` | The wait becomes part of the fun, and shoppers can see the Bulldog is working, so they stay for the answer. |
| **Friendly loaders**: "Sniffing out every hoodie and tee…" on product lists and pages. | `Brand.tsx` (`BulldogLoader`) | Keeps the same voice everywhere, so loading never looks broken. |
| **Reduced motion**: every animation turns off for shoppers who ask their device for less motion. | `index.css`, `index.html` | Keeps the site comfortable and accessible for everyone. |

## Notes

- The Handsome Dan, shield, and wordmark are **original illustrations inspired by** Yale's mascot and colors, not Yale's trademarked logos. As a licensed Yale retailer, Campus Customs would swap in the official artwork it receives under its license.
- Checked in the browser:
  - Home, About, product pages, and chat render with both fonts loaded.
  - The chat header and the agent's replies say "Bulldog Assistant".
  - The waiting animation runs while the reply streams in.
