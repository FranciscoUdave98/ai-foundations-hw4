# AI Prompts

## Problem 1: Vibe coder prompts

### Initial prompt

> Today i'm working on Homework 4 so use the skill to create a virtual environment and put all of my stuff there

### Extra instructions

> For "Problem 1: Vibe coder prompts" you will create AI\_prompts.md and update it as I work through this homework. For each of the 13 problems you will log the problem number and title, the prompts I typed and summarize any follow-ups for each problem

### Homework context

> Also log the context for this homework. I've uploaded the data we'll use to the folder. We'll create a Campus Customs customer website with a chatbot. For this we will use a React + Vibe TypeScript front end and a Python FastAPI backend with a PydanticAI agent. Shoppers will be able to browse products, create accounts, chat about merch, see the items that match, and get helpful answers about price and stock. Check out this page to learn more about Campus Customs style. For the agent AI calls we'll use OpenAI through Portkey and use the Terra model. In the end we'll push our project to a public GitHub repo so set everything up to do that. Database and product images will not be included in the repo

### Summary of changes

Set up the existing `HW4/` folder with the `lecture-setup` skill's templates (`joke.py`, `requirements.txt`, `.gitignore`, `README.md`), created a Python 3.13 virtual environment in `HW4/.venv`, installed requirements, and ran the `gpt-5.6-luna` joke smoke test (saved to `today_joke.txt`). Created this prompt log.

Logged the homework context: a Campus Customs shopper website with a chatbot, built as a React + Vite TypeScript front end and a Python FastAPI backend running a PydanticAI agent. Unzipped `data.zip` into `data/`, which contains `campus_customs.db` (tables: `catalogue` with 102 products, `inventory` with 612 size/quantity rows, `users`, `chat_messages`) and 102 product photos in `data/products/`. Confirmed `gpt-5.6-terra` works through Portkey. Prepared for a public GitHub repo: ran `git init -b main`, added `.env.example`, and extended `.gitignore` so the database, product images, `data.zip`, `.env`, `.venv`, and `node_modules/` are never committed. Nothing has been pushed yet.

## Problem 2: Analyze the database

### Initial prompt

> For "Problem 2: Analyze the database" please look at the database and make visuals for catalogue, inventory, and users so I can understand it. Create the file output/harness.md and write each table, its fields, and a short line on why each field matters for the shop or the chatbot

### Summary of changes

Wrote `analyze_database.py`, which profiles `data/campus_customs.db` and generates `output/database_overview.html`: a self-contained, blue-themed interactive dashboard (hover tooltips, table views, light/dark mode) with a schema map, catalogue charts (products by category, price points, top colors), inventory charts (stock-level distribution, units by size, sold-out heatmap by category and size, most sold-out products), and a users section (accounts table with masked emails, chat messages per user). Created `output/harness.md` documenting every field in `catalogue`, `inventory`, `users`, and `chat_messages` with why it matters for the shop or chatbot.

### Findings

`garment_type` has 22 inconsistent labels (grouped into 6 categories), colors mix `navy`/`navy blue`, price is fixed by garment type (7 price points, $32–$98), and 145 of 612 size rows (24%) are sold out, so stock answers must be checked per size. Emails are masked and password hashes omitted from the report because it will be in the public repo.

## Problem 3: Build the Campus Customs website

### Initial prompt

> For "Problem 3: Build the Campus Customs website" you will scaffold a React + Vite + TypeScript front end. Make sure to create a navigation bar at the top with tabs for Home, Products, About Us, Log in, and Create account. Use the style wording from the website I uploaded earlier for Home and About Us, but don't copy it. Instead, paraphrase it in a nice way so it is attractive for prospective buyers (Yale students)
>
> Then, on the products page you will show images from the catalogue using the paths in the database and include basic product info like name, price, short description, etc.
>
> When you click each product it should create a single-item page. It should have a large image on one side, full product text  on the other (description, price, sizes and stock if available).
>
> In the bottom right of the site add a chat interface. No need to call agent yet. We'll also need a small API so start a simple FastAPI app in backend/main.py and well make it better later

### Summary of changes

Scaffolded `frontend/` with Vite (React + TypeScript) and React Router. Added a sticky Yale-blue navigation bar (Home, Products, About Us, Log in, Create account; collapses to a menu on phones), a Home page (hero with product photos, "why students shop with us," featured picks, shop-by-style links, residential-college banner), an About Us page (story timeline, values, services, visit info), a Products page (image grid with name, category, short description, price, colors, sold-out badge, search, and category filters), single-item pages at `/products/:id` (large photo on the left; description, price, style, colors, availability, and size buttons showing stock on the right), Log in and Create account forms (UI only for now), and a bottom-right chat widget (Enter to send, typing indicator) that posts to a placeholder endpoint.

Created `backend/main.py` (FastAPI): `/api/health`, `/api/products`, `/api/products/{id}` with per-size stock, a placeholder `/api/chat`, and `/images/products/...` serving photos from the database's `image_file_path`. Only the photos folder is served, never the database. Added `fastapi`, `uvicorn`, and `pillow` to `requirements.txt`.

### Problems encountered

- No style page had been linked, so the Home and About Us copy paraphrases the official Campus Customs site (campuscustoms.com) and public descriptions of the store (founded 1975 across from campus, family-run, printing and embroidery done in-house, open seven days).
- Product photos have mixed black (73) and white (29) backgrounds, so the API samples each photo's corner color and the frames match it. Some photos have black bars baked into the image itself.
- Three catalogue rows have placeholder descriptions ("Vision blocked; filename-based stub") and no colors, so the API shows friendly fallback copy instead.
- Product names built from file names were tidied for display (e.g. "1 4 Zip" → "1/4 Zip", "Creqneck" → "Crewneck").
- Fixed a phone-width overflow on product pages and two React lint warnings.

### Follow-ups

> I don't like interchanging between black and white backgrounds so change all backgrounds to white (of the products)

Wrote `whiten_backgrounds.py`, which backs up the originals to `data/products_original/` (git-ignored) and rewrites the 76 photos with black backgrounds or side bars to white. It flood-fills the near-black area connected to the photo's edge, closes the thin gray seams where black bars met white, and feathers the edge. Black logos and details inside the garments are untouched. Checked all 102 photos on a contact sheet and zoomed in on dark garments to confirm clean edges. Removed the per-photo frame color from the API and site, so every product frame is now white, with a thin divider under each card photo.

## Problem 4: Create account and login

### Initial prompt

> For "Problem 4: Create account and login" create a normal flow asking First name, Last name, email, password, and confirm password for create account. For the log include email and password. When someone creates a new account it should go into the "users" table. Make sure that you store the passwords securely so that hackers can't access them. In the seed database include test@campuscustoms.yale.edu and password=password. I'll confirm that I can log in and create a new account. Update output/harness.md to explain how the authorization works (how you are protecting passwords and what you store for each user)

### Summary of changes

Added `backend/auth.py` with `/api/auth/register`, `/login`, `/logout`, and `/me`, plus `backend/db.py` for shared SQLite connections. New accounts are inserted into `users` (first name, last name, full name, lower-cased email, password hash). Passwords are hashed with salted PBKDF2-SHA256 at 600,000 iterations; the seed database's older 120,000-iteration hashes still work and are upgraded on the next login. Sessions use a random token in an HttpOnly, SameSite=Lax cookie, with only the token's SHA-256 stored in a new `sessions` table. Login errors don't reveal whether an email exists, and 5 failed attempts in 15 minutes trigger a temporary lockout. The API makes sure `test@campuscustoms.yale.edu` / `password` always exists.

On the front end, the Log in and Create account pages now call the API, show inline validation errors and server messages, and redirect to Products after success. The nav bar shows "Hi, First name" and Log out when signed in, and the session survives a page reload. Documented the flow, password protection, session protection, and stored fields in `output/harness.md`.

### Testing

Tested against a copy of the database and in the browser: seed login, wrong password, unknown email, duplicate email, mismatched and short passwords, invalid email, brute-force lockout, logout, staying logged in after a reload, and confirming page scripts can't read the session cookie. A throwaway account created during browser testing was deleted afterwards, so `users` still has only the original 3 accounts.

## Problem 5: PydanticAI agent backend

### Initial prompt

> For "Problem 5: PydanticAI agent backend" we'll build the shop chatbot as a PydanticAI agent using FastAPI. The API app should be in backend/main.py which will run with uvicorn. The agent will have 4 files 1) backend/prompts/prompt.md which is the system prompt, 2) backend/agent.py, 3)backend/tools.py, and backend/models.py
> In main.py there should be a chat route so that a message from the website returns a reply from the agent and whatever else is needed for products or auth. The agent should be able to access the API key.
> Then, let's put Campus Customs voice and safety basics into prompts/prompt.md (you can reutilize from previous homeworks). Make sure to update structured data types in models.py for chat replies and product cards as we work through these problems.
> FInally, in output/harness.md explain how the front end talks to FastAPI and how the agent is loaded from the prompt file and model
> The model should run in the terminal with this command: uvicorn main:app --reload --port 8000

### Summary of changes

Built the shop agent in four files:
- `backend/prompts/prompt.md`: role, Campus Customs voice, tool rules, and safety basics adapted from HW3's safety section.
- `backend/agent.py`: loads the Portkey key from `.env`, uses `OpenAIChatModel("gpt-5.6-terra")` through Portkey, and runs a PydanticAI `Agent` with `ShopReply` output, per-request shopper context, and four tools.
- `backend/tools.py`: catalogue search with filters, product details, stock by size, and a catalogue overview, reading live from SQLite. The website routes use the same functions.
- `backend/models.py`: `ProductCard`, `ProductDetail`, tool result types, `ChatRequest`, `ShopReply`, `ChatReply`, and `ChatHistoryMessage`.

`backend/main.py` now has `POST /api/chat`, which runs the agent and turns the product ids it returns into verified product cards. It also has `GET /api/chat/history`, and it saves chats for logged-in shoppers to `chat_messages`. The backend switched to plain imports so `uvicorn main:app --reload --port 8000` runs from `backend/`.

The chat widget sends the conversation and the current product page, renders simple Markdown, shows product cards under replies, and restores saved chats after login. Documented the front-end-to-FastAPI flow and how the agent is loaded in `output/harness.md`.

### Problems encountered

- A prompt-injection test was blocked by the model provider's content filter and surfaced as "assistant unavailable". The route now answers those with a polite on-topic reply.
- "Crewnecks for my mom" missed the Yale Mom Crewneck, and the agent read the `colors` list as color options ("comes in gray or navy"). The prompt now tells it to search with the shopper's specific words (family, college, sport designs) and that each product is a single colorway.
- Prompt edits didn't apply until a restart (uvicorn only watches `.py` files), so the agent now re-reads `prompt.md` on every run.
- Test chat messages and sessions created during browser testing were removed from the database afterwards.

## Problem 6: Tools: product info and stock

### Initial prompt

> For "Problem 6: Tools: product info and stock" we are giving our agent tools to look up information from campus_customs.db
> These will include Product description, price, and how many are in stock
> Warning: The agent MUST use the database. Under no circumstances should the agent invent prices or quantities. If a size is out of stock the agent should communicate so clearly.
> Include these tools in the prompt so the agent knows how to call them and actually uses them for any stock and price questions. Make sure to update our models.py with the structured data types
> Finally, in output/harness.md create a list of each tool and explain what model fields we are using  for lookup results and why. Make sure that these lookups are unique so there are no duplicate answers for a specific lookup

### Summary of changes

Split the agent's lookups into one tool per fact:
- `search_products` finds product ids only, with no prices or stock.
- `get_product_info` returns the description and style.
- `get_prices` returns `catalogue.price`.
- `get_stock` returns `inventory.quantity` per size, with a status of in_stock, low_stock, sold_out, or not_offered and a plain "SOLD OUT" message.
- `catalogue_overview` is unchanged.

Added the structured types to `models.py`: `StockStatus`, `SizeStock.status`, `ProductMatch`, `ProductInfo`, `PriceQuote`, `PriceLookup`, `StockLookup`, and `StockLookupResult`. The prompt now has a tool table, example call flows, and hard rules: never invent numbers, look them up every turn, and say "sold out" clearly.

Added a code-level guard in `agent.py`: every tool records what it returned, and an output validator rejects replies with prices or quantities the tools didn't return this turn, or that don't state a sold-out size. The agent is then told to look it up and retry. Lookups are unique: the database keys (`product_id` primary key, `UNIQUE (product_id, size)`) plus de-duplication of repeated ids and size normalization mean each lookup has exactly one answer. Documented every tool, its result fields and why, uniqueness, and enforcement in `output/harness.md`.

### Testing

17 offline checks passed, including a scripted fake model that invented "$19.99", got rejected, called `get_prices`, and answered "$32". Six live questions with gpt-5.6-terra all used the tools and gave numbers that match the database. One of them (XXXL on a product page) was sent back once by the guard until it clearly said the size isn't offered.

## Problem 7: Chat search that updates the page

### Initial prompt

> For "Problem 7: Chat search that updates the page" we will improve our webpage so that when  a customer asks about an item, the agent searches the catalogue and the page automatically updates live showing the available matching options and showing the items products card (with image, name, price, and short info) that match
> To be clear, the agent should return structured product matches and the front end should render them on the website

### Summary of changes

**Backend:** the agent's output (`ShopReply`) now returns structured matches: `results_title` plus a list of `ProductMatchRef` (`product_id` + a short `why` note). The output validator checks the notes and title for invented prices or quantities, the same as the reply, and removes repeated or unknown ids. `/api/chat` returns `MatchedProduct` cards built from the live database (image, name, price, short description, sizes in stock, match note). The prompt has a new "Showing matches on the page" section.

**Front end:**
- A shared `ChatResultsProvider` holds the latest matches.
- When a reply includes products, the site goes to the Products page. There a new `ChatResults` section renders the cards live, with the title, match count, notes, sizes in stock, a highlight animation, and a Clear button.
- Questions about the product on screen don't navigate away.
- Chat replies show 3 mini cards and a "See all N on the page" button.
- On wide screens the page makes room for the open chat.

### Problems encountered

- A follow-up for "sport design" hoodies returned gray hoodies with navy print, because the color filter matched any color on the garment. Every product lists its fabric color first, so the `color` filter now matches the main color by default. There is a `color_anywhere` option for print colors, and search results expose `main_color`.

### Testing

The offline checks still pass, including an invented price hidden in a match note. In the browser with the live model:
- A question on Home switched to the Products page with 8 correct navy hoodie cards.
- A follow-up updated the section live to 2 sport hoodies.
- A product-page question stayed on that page.
- A non-product question left the matches in place.
- The chat panel doesn't overlap the cards at 1440px.

## Problem 8: Customer memory

### Initial prompt

> Now, for "Problem 8: Customer memory" when a customer is logged in, save their chat history in the database appropriately so that you can reload it when he returns. The agent should know who is chatting (name and email). Make sure to put that in the agent dependencies and in the tools the agent can call.
> Finally, pass enough page context so that when someone asks about a product the agent knows what product they refer to. You can put code into the agent context.
> This does not mean that guests can't chat, but only history is saved for logged in users. Write in the harness.md how history is stored, what customer fields the agent can see and how you the agent is parsing the page context

### Summary of changes

- **New `backend/memory.py`:** a startup migration (adds `results_title` and `page_context_json` to `chat_messages`, plus a `(user_id, id)` index), one-transaction saving of each turn for logged-in customers, history loading, the customer profile, past products, and clearing history. Guests are never saved.
- **Agent dependencies:** `ShopDeps` now holds the logged-in `Customer` (first/last name, email, member since) and the validated `PageContextInfo`. `describe_customer()` and `describe_page()` write them into the agent's instructions every run. New tools: `get_customer_profile`, `get_past_products`, and `get_page_context`. None of them take a user id, so they can only read the current customer.
- **Page context:** the browser sends a structured `PageContext` (page type, product, filters, numbered on-screen matches, recently viewed). `resolve_page_context()` checks every id against the catalogue, renumbers positions, validates the category, and trims search text, so "this", "the second one", and "the one I looked at before" resolve to real products.
- **Routes:** `/api/chat` uses the database history for logged-in customers. `/api/chat/history` returns ids and results titles. New `DELETE /api/chat/history`.
- **Front end:** `pageContext.ts` builds the page context and tracks recently viewed products. The chat shows "Signed in as … · chat is saved" or "Guest · log in to save this chat", greets returning customers with "Welcome back", and has a Clear history / Start over button.
- **Docs:** documented history storage, visible customer fields, and page-context parsing in `output/harness.md`.

### Problems encountered

- On-screen positions skipped a number when an invalid id was dropped ("1., 3."). They're now counted over valid products only.
- Test-only: a second test client runs on a new event loop, so the cached agent had to be rebuilt between clients. uvicorn uses a single loop, so the app is unaffected.

### Testing

22/22 checks passed on a scratch copy of the database with the live model: page-context validation, the migration, a guest chat that isn't saved, the agent knowing the logged-in email, saving with title, notes, and page context, "the second one", history reloading and past-product recall in a new session, and clearing only that customer's history. A browser test on the real site confirmed "Welcome back", the restored chat, and the page and past references. The test exchange was then deleted from the database.


## Problem 9: Usability improvements

### Initial prompt

> For "Problem 9: Usability improvements" make the next improvements
> Frontend
> 1) When looking at a product add under it a carrousel of related products so that a customer can look similar items to the product shown
> 2) For the photos generate a model wearing each product and make zooming in available
> Backend
> 1) The agent should not just show 3 points when thinking, it should inform the user with fun and clever messages like "Checking availability", "Searching for Medium sizes" but make them more memorable and funny
> 2) To make the model cheaper make the agent decide the difficulty of the question and choose between Terra and a cheaper OpenAI model so that it runs more cost-efficient
> In outputs/usability.md write what we added and how it helps Campus Customs customers

### Follow-ups

- Asked how many on-model photos to generate: "how much do you estimate it will cost". Chose the model: gpt-image-2.
- After the estimate (≈$0.02 low, ≈$0.065 medium, ≈$0.22 high per photo): "low 60% of products only".
- After finding the Portkey key can't reach any image model: "Skip AI photos for now".

### Summary of changes

- **Related products:** a "You might also like" carousel under every product page (`RelatedCarousel.tsx`, `GET /api/products/{id}/related`). Items are scored by shared college, sport, or family theme, then style, rare tags, color, and price. Each card has a reason chip.
- **Zoom:** a new product gallery with hover magnification and a full-screen zoom viewer (100–350%, wheel, buttons, keys, drag to pan). It shows "Product / On model" thumbnails whenever `data/on_model/<id>.jpg` exists.
- **On-model photos:** the prompt (`imagegen/on_model_prompt.txt`) and a 61-product list (60%, spread across categories) are ready for gpt-image-2 at low quality (~$1.20 total). No photos were generated this round, because the course Portkey key only routes to chat models.
- **Thinking messages:** `status.py` sends fun, specific status lines from each agent step and tool ("Hunting for Larges. They vanish faster than move-in week snacks…"). They stream through the new `POST /api/chat/stream`, and the chat widget shows them live next to the typing dots.
- **Cost routing:** a Luna router labels each question simple or complex. Simple questions run on `gpt-5.6-luna` (10× cheaper than Terra per OpenAI's pricing page), complex ones on `gpt-5.6-terra`. If Luna's answer fails the guardrails, the question is retried on Terra. Every answer's model and tokens are logged in a new `agent_runs` table.
- **Write-up:** `output/usability.md` (in the existing `output/` folder) explains each change and how it helps customers.

### Problems encountered

- The imagegen skill's built-in tool isn't available here, and its API path failed through Portkey ("Unexpected deployment name…" / "imageGenerations operation does not work with the specified model gpt-5.6-…"). Every image request is routed to a chat deployment, so photo generation was skipped with your approval.
- The Portkey key quietly maps unknown model names (`gpt-5.4-nano`, `gpt-5-mini`) to Luna. `gpt-5.4-mini` worked, but OpenAI's pricing page showed Luna is cheaper ($0.20/$1.20 vs $0.75/$4.50 per million tokens), so Luna became the cheaper model.
- PydanticAI 2.x exposes `result.usage` as a property. Calling it as a method made the router silently fall back to Terra until this was fixed.
- The on-screen check found the related-reason chips wrapping onto two lines, so they were shortened ("Same style & color").

### Testing

With the live models, all 6 test questions routed as expected:
- Luna: greeting, one price, "is this in M?", "show me hoodies".
- Terra: a multi-constraint gift request and a two-product comparison.

Tool-specific status lines streamed each time. On these 6 questions, routing cost ≈$0.083 versus ≈$0.169 all-Terra, about 50% cheaper and about 90% cheaper per simple question.

An offline test forced the cheap model to keep inventing a price; it escalated to Terra, which answered with the real $32.

Browser checks:
- Hover zoom, the lightbox at 250%, and Esc to close all worked.
- The carousel rendered 12 related cards.
- The chat showed live status lines before answering.


## Problem 10: Style the website

### Initial prompt

> For "Problem 10: Style the website" you'll use white Yale navy colors, rename the agent to "Bulldog Assistant" and add Handsome Dan and Yale University svg throughout the page. Make sure to use fun typographies and motions whenever a new page is loading. Also update the chatbox so the loading or ... show a fun logo or image while the customer is waiting
> In output/design.md you will describe these changes and why it helps customers stick around and buy. It should be short and concrete

### Follow-ups

> done yet?

(Answered with a status update and finished the visual check, `design.md`, and this log.)

### Summary of changes

- **Palette:** Yale navy (#00356B) and white only.
- **Art:** original SVG art in `components/Brand.tsx`: a Handsome Dan face, and a full Dan with a "Y" collar, a "Y · 1701" shield, a "YALE UNIVERSITY" wordmark, paw prints, a paw trail, and a Bulldog loader. It's used in the navbar, favicon, hero, banners, promises, About, footer, auth pages, 404, and chat.
- **Fonts:** Graduate (varsity) and Fraunces (playful serif), bundled locally with `@fontsource`.
- **Motion:**
  - a Handsome Dan splash in `index.html` while the app loads;
  - a navy progress bar with trotting paws on every page change;
  - page slide-in, "stamp" headlines, and staggered cards;
  - a scrolling "Go Bulldogs" ribbon;
  - everything turns off with the reduced-motion setting.
- **Chat:** renamed "Bulldog Assistant" in the widget and the system prompt. It has a Dan avatar next to replies, an "Ask the Bulldog" launcher, and an animated Dan (bobbing, ear flaps, sniffing nose) with a walking paw trail instead of the "…" while waiting. A new "Ask the Bulldog" hero button opens the chat.
- **Write-up:** `output/design.md`: what changed and why it keeps shoppers around and buying.

### Problems encountered

- The first Handsome Dan sketch looked like a pug. It was redrawn with drooping jowls, a big nose, and an underbite with fangs.
- The screenshot check showed the "Ask the Bulldog" hero button had invisible text (the default button background), and the splash tagline picked up the product-tag style. Both were fixed.
- The illustrations are original and inspired by Yale, not Yale's trademarked logos; this is noted in `design.md`.


## Problem 11: Site testing (app check)

### Initial prompt

> For "Problem 11: Site testing (app check)" document the live site in output/app_check.html that includes screenshots and captions for 1) the chat checking the inventory level of an item, 2) the dynamic search result cards appearing after a category question, and 3) the usability features we included in Problem 9.
> Make the html easy to grade including heading for each check, screenshot and one or two sentences on what it proves. Save the screenshots in output/app_check_images/ and link them from app_check.html with relative paths

(Francisco attached 5 screenshots of the live site.)

### Follow-ups

> Include any screenshots you take that you think should also be here

> done?

> cant find the file

(Pointed to `HW4\output\app_check.html` and opened it in the browser and in File Explorer.)

> delete 2nd picture in check 3a and first picture in check 3b

(Removed the full product page screenshot from 3a and the "Click to zoom" badge screenshot from 3b, deleted both image files, and reworded the 3b caption.)

### Summary of changes

- **Report:** created `output/app_check.html`, with a table of contents and a heading, Pass badge, screenshot, and 1–2 sentence "what it proves" caption for each check. All images link with relative paths to `output/app_check_images/`.
- **Francisco's screenshots (01–05):**
  - the inventory check on the Baseball Left Chest Crewneck, verified against the database (S 15, M 5, L 25, XXL 25, XS/XL 0);
  - the "Gray crewnecks" dynamic cards;
  - the related carousel;
  - the fun thinking status;
  - the zoom badge.
- **Added by Claude (06–08):**
  - a full product page showing the gallery and the "Also Benjamin Franklin" carousel;
  - a rendered backend log of the 11 live answers (9 Luna, 2 Terra; ≈$0.12 vs ≈$0.49 all-Terra, ≈75% less);
  - the full-screen zoom viewer at 250%, panned to the crest.
- **Capture method:** headless Edge driven through the DevTools protocol for the interactive zoom and pan.

### Problems encountered

- Capturing the zoom viewer revealed a Problem 10 regression. The page-entrance animation left a transform on the page, so the fixed-position viewer was trapped under the navbar and clipped. Fixed in two ways:
  - the animation now uses `backwards` fill, so no transform is left behind;
  - the viewer renders into `<body>` through a React portal.
- Two quick zoom clicks registered as one (175%), so the capture script now waits between clicks.


## Problem 12: Audit trail, safety, finish harnesses

### Initial prompt

> For "Problem 12: Audit trail, safety, finish harnesses" create an append-only output/audit_trail.json of agent-loop activity (time, tool name, short args/result, reason)
> Also include these safety rules in prompts/prompt.md and make sure the agent knows how to follow them
> 1) Never invent product facts
> 2) Confirm high-impact actions with the customer so the agent doesn't for example add a product to the cart without the customer's explicit authorization
> 3) Never store sensitive information from the customers and minimize personal data
> Then, update output/harness.md so it shows clearly how the system works. This should include model fields in models.py and why you chose them, tools and abilities we created, safety rules, and specs such as loop limits , result caps, models, and how to run front and back)

### Follow-ups

> done?

(Answered with a status update and continued.)

### Summary of changes

- **Audit trail:** `backend/audit.py` writes `output/audit_trail.json`, a valid JSON array. It's append-only (only the closing bracket is rewritten) and hash-chained (`prev_hash` → `hash`, checked by `audit.verify()`).
  - **Events:** `run_start`, `route`, `tool_call`, `tool_error`, `guardrail_retry`, `escalate`, `run_end`, and the site's `cart_add` / `cart_remove`.
  - **Wiring:** every agent tool is wrapped by `@audited`, and each tool takes a `reason` argument the agent fills in. Results are summarized briefly, with no message text, names, or emails.
- **Rule 2, confirm high-impact actions:** `backend/cart.py` adds a bag (logged-in customers only) and pending actions. The agent tools are `view_cart`, `propose_add_to_cart` (adds nothing), `confirm_add_to_cart` (only after a clear yes in a *later* message, checked in code), and `cancel_pending_action`. The validator rejects "added to your bag" without a confirmed add. The front end has a Bag page, a navbar bag count, and a Remove button.
- **Rule 3, sensitive data:** `backend/privacy.py` removes card numbers (Luhn-checked), security codes, SSNs, passwords, and phone numbers before the model, history, or audit trail see them; the agent is told when something was removed.
- **Prompt:** `prompts/prompt.md` has a new "Safety rules (always follow)" section for the three rules, with the propose → confirm flow spelled out, and the new tools are in the tool table.
- **Docs:** `output/harness.md` was rewritten as a system guide: architecture, how to run, models and routing, the agent loop and limits, tools, the `models.py` fields and why, safety enforcement, the audit format, caps, and stored data. The per-problem notes are kept as an appendix.

### Testing

On a scratch copy of the database, with the live model:
- A guest asked to add to the bag was told to log in.
- The first request only proposed the add ("Add 1 × Boola Boola T-Shirt, size M, $32, to your bag?"), and "Yes please" added it.
- A card number was removed from the stored chat and never reached the audit trail.
- The audit chain verified, and a tampered copy failed verification.

The gate unit test refused a same-turn confirmation, a vague reply, and a replay, and accepted a clear later "yes". Two real guest chats seeded `output/audit_trail.json` (12 entries, chain valid).


## Problem 13: Push to GitHub and submit the URL

### Initial prompt

> For "Problem 13: Push to GitHub and submit the URL" put everything in hm4 and push it to a public GitHub repo. Use this structure and don't include .env, campus_customs.db Use .gitignore and include .env.example with placeholders

(Francisco attached the expected layout: `hw4/` with `AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `frontend/`, `backend/` (`main.py`, `agent.py`, `models.py`, `tools.py`, `prompts/prompt.md`), and `output/` (`harness.md`, `design.md`, `usability.md`, `app_check.html`, `app_check_images/`, `audit_trail.json`), with `data/` kept local.)

### Summary of changes

- **Repo root:** the `HW4` folder is the repo root, in the requested layout. The backend's supporting modules (`auth.py`, `db.py`, `memory.py`, `cart.py`, `privacy.py`, `audit.py`, `status.py`) sit next to the required files in `backend/`.
- **`.gitignore`:** now ignores the whole `data/` folder (database and product images), plus `.env`, `.venv/`, `node_modules/`, `dist/`, caches, and `tmp/`.
- **`.env.example`:** placeholders only (`PORTKEY_PAI_KEY=your-portkey-key-here`, plus optional commented lines).
- **Checks before pushing:** reviewed the 70 files to be committed. None contains the API key, and none is a `.db`, `.env`, or under `data/`.
- **README:** points to `output/harness.md` and lists the new files.
- **Push:** committed and pushed to the public repo **https://github.com/FranciscoUdave98/ai-foundations-hw4**.
