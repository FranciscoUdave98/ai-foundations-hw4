# Usability improvements (Problem 9)

What we added to the Campus Customs site and chatbot, and how each change helps shoppers (mostly Yale students and their families).

## Front end

### 1. "You might also like" carousel on every product page

**What it is:** a swipeable row of up to 12 similar products under each product page. Each card shows the photo, name, price, and a short reason chip: "Also Benjamin Franklin", "Also Dad", "Same style & color", "Same style", or "Same color".

**How it picks items** (`tools.related_products`, served by `GET /api/products/{id}/related`):
- **Shared theme (strongest):** the same residential college, school, sport, or family word, e.g. Benjamin Franklin 1/4 Zip → Benjamin Franklin Fleece Jacket and T-Shirt; Yale Dad Hoodie → Yale Dad Crewneck and T-Shirt.
- Then: same category, rare shared tags (tags on most products, like "yale", are ignored), same main color, and a price within $15.
- Sold-out items drop to the end.

**Controls:** arrow buttons (disabled at the ends), trackpad or touch swipe with scroll snapping, and keyboard focus on each card.

**Why it helps customers:**
- A student who likes their college's quarter-zip finds the matching tee or fleece in one click.
- A parent shopping for "Dad" sees every Dad item together.
- If a size is sold out, close alternatives are right there, so fewer shoppers leave empty-handed.

### 2. Photo zoom and on-model photos

**What it is (`ProductGallery.tsx`):**
- **Hover to magnify:** the product photo zooms 2.2× around the cursor to show crests, stitching, and lettering.
- **Click for full-screen zoom:** zoom from 100% to 350% with the buttons, the mouse wheel, `+`/`-`, or a double-click. Drag to pan; Esc or a click outside closes it.
- **On-model photos:** when a product has one, the gallery shows **Product / On model** thumbnails, and the zoom viewer can switch between them with the arrow keys. The API lists photos in `ProductDetail.images` and serves them from `/images/on_model/`.

**Why it helps customers:**
- Merch is bought for the details (the right college crest, the lettering, the fabric), and zoom lets shoppers check them before buying.
- On-model photos show fit and length, which a flat product shot can't.

**Status of the AI on-model photos:** the site is ready, but none have been generated yet.
- **Why:** the course Portkey key is routed to chat models only, so every image model (`gpt-image-2`, `gpt-image-1-mini`, …) returns an error. We skipped generation for now.
- **What's ready:**
  - the prompt: `imagegen/on_model_prompt.txt`, a faithful copy of the garment on one adult model against a plain studio backdrop;
  - the product list: `imagegen/on_model_products.txt`, 61 products = 60% of the catalogue, spread across categories and favoring the best-stocked items, and skipping the 3 whose photos the safety filter blocked in HW3.
- **Planned run:** `gpt-image-2`, low quality, 1024×1024, estimated at about $0.02 per photo, so **about $1.20** for all 61. The README has the command, which uses the imagegen skill's CLI with an image-enabled `OPENAI_API_KEY`.
- **After the run:** each photo appears on its product page automatically. Photos are kept in `data/on_model/`, which is not committed, like the other product images.

## Back end

### 1. Fun, specific "thinking" messages instead of three dots

**What it is:**
- **Live streaming:** the chat now calls `POST /api/chat/stream`, which streams status lines (newline-delimited JSON) while the agent works, then the answer.
- **Tied to real steps:** each step and tool announces what it's actually doing (`backend/status.py`), filled in with the shopper's own search terms, and never repeats the same line twice in a row.

| When | Example messages |
|---|---|
| Reading the question | "Reading your question like the last page of a blue book…", "Sizing up your question (pun fully intended)…" |
| Quick vs. expert model | "This one's a layup. Grabbing it now…" / "Ooh, a thinker! Calling in the senior Bulldog…" |
| Searching | "Asking Handsome Dan to sniff out Boola Boola tee…", "Rummaging through the Broadway stockroom for Hoodies…" |
| Searching by size | "Hunting for Larges. They vanish faster than move-in week snacks…", "Measuring twice, searching for Mediums once…" |
| Searching by color | "Sorting the navy gear from the rest of the rack…" |
| Checking stock | "Asking the stockroom: any Mediums left?", "Doing inventory faster than a Commons lunch line…" |
| Checking prices | "Reading the price tags (no haggling, we promise)…", "Checking prices. Sadly there's no Harvard discount…" |
| Guardrail recheck | "Our fact-checker (strict, like a TA) wants one more look…" |
| Customer memory | "Flipping back through our chat notebook…" |
| Finishing | "Wrapping it up with a bow (Yale blue, of course)…" |

**Why it helps customers:**
- Waiting feels shorter and more transparent, because shoppers see the assistant is actually checking sizes and prices, not stalling.
- It also shows the answer comes from real stock ("any Mediums left?"), which builds trust.
- The Yale and New Haven humor fits the family-shop voice.

The original `POST /api/chat` still works for anything that doesn't need streaming.

### 2. Cheaper answers: the agent picks Terra or a cheaper model per question

**How it works (`agent.run_chat`):**
1. **Router:** a small `gpt-5.6-luna` call reads the new message plus light context (page type, how long the chat is, the start of the last reply) and returns a structured `RouteDecision {difficulty: simple | complex, reason}`.
   - *Simple:* a greeting, store info, one product's price, "is this in M?", or a plain search with one filter.
   - *Complex:* gifts and recommendations, two or more constraints, comparisons, follow-ups that depend on earlier messages, and anything uncertain. When in doubt, it picks complex.
2. **Simple → `gpt-5.6-luna`, complex → `gpt-5.6-terra`.** It's the same agent, prompt, tools, and guardrails; only the model changes (`agent.run(model=…)`).
3. **Safety net:** if the cheaper model can't produce a verified answer (the Problem 6 guard keeps rejecting it, or it hits the step limit), the question is retried once on Terra ("Getting a second opinion from the expert…"). If the router itself fails, the question goes to Terra.
4. **Logging:** every answer is logged in a new `agent_runs` table with the model, difficulty, reason, tokens, and escalation. It stores no message text or customer id, so the savings can be measured.

**Why Luna as the cheaper model:**
- OpenAI's [pricing page](https://developers.openai.com/api/docs/pricing) lists Terra at $2.00 per million input tokens and $12.00 per million output. Luna is $0.20 and $1.20, so **10× cheaper**, and it's the same GPT-5.6 generation (and the default model in `AGENTS.md`).
- `gpt-5.4-mini` ($0.75 / $4.50) also works on our Portkey key but costs more than Luna.
- Other "mini/nano" names silently fall back to Luna on this key.

**Measured results** (6 live questions, token counts from `agent_runs`):

| Question | Routed to | Tokens in / out |
|---|---|---|
| "Hi there!" | Luna | 7,144 / 148 |
| "How much is the Boola Boola tee?" | Luna | 11,196 / 217 |
| "Is this in M?" (on the Yale Dad Hoodie page) | Luna | 7,249 / 206 |
| "Show me hoodies" | Luna | 13,996 / 719 |
| "Gift for my dad under $70, loves baseball, wears a large" | Terra | 13,367 / 809 |
| "Compare the Champion crewneck and the Basic hoodie…" | Terra | 16,542 / 368 |

| | Cost of these 6 answers |
|---|---|
| Everything on Terra | ≈ $0.169 |
| With routing | ≈ $0.083 |
| **Savings** | **≈ 50% overall; ≈ 90% on each simple question** (≈ $0.0024 instead of ≈ $0.024) |

Each routing decision costs about $0.0001 on Luna. How much Campus Customs saves depends on the mix: the more simple price and stock questions, the bigger the savings. All six routed as expected, and all answers still passed the database guardrail. An offline test forced a bad answer from the cheap model and confirmed the switch to Terra; the final answer had the real $32 price.

**Why it helps customers:** Campus Customs can keep the chat open to every shopper, including guests, at about half the cost. Quick questions still get quick, accurate answers, and harder ones still get the stronger model.

## Files

| Area | Files |
|---|---|
| Related products | `backend/tools.py` (`related_products`), `backend/main.py` (`/api/products/{id}/related`), `frontend/src/components/RelatedCarousel.tsx` |
| Zoom and on-model photos | `frontend/src/components/ProductGallery.tsx`, `backend/tools.py` (`product_images`), `backend/models.py` (`ProductImage`), `imagegen/` (prompt + product list) |
| Thinking messages | `backend/status.py`, `backend/main.py` (`/api/chat/stream`), `frontend/src/api.ts` (`sendChatStream`), `frontend/src/components/ChatWidget.tsx` |
| Model routing | `backend/agent.py` (`route`, `run_chat`, `ROUTER_PROMPT`), `backend/models.py` (`RouteDecision`, `ChatReply.answered_by`), `backend/memory.py` (`agent_runs`, `log_run`) |
