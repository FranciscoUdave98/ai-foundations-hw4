# Campus Customs Shop - AI Foundations for Managers Homework 4

Francisco's Homework 4 for AI Foundations for Managers (Yale): a Campus Customs customer website with a shopping chatbot.

- **Front end:** React + Vite + TypeScript
- **Back end:** Python FastAPI with a PydanticAI agent
- **AI:** OpenAI SDK through Portkey; a router sends simple questions to `gpt-5.6-luna` and complex ones to `gpt-5.6-terra`

Shoppers can browse products, create accounts, chat with the **Bulldog Assistant** about merch, see matching items, ask about price and stock, and keep a bag (the assistant only adds items after the shopper confirms).

**Full system guide:** [`output/harness.md`](output/harness.md) (architecture, models, loop limits, tools, data types, safety rules, audit trail). Also see [`output/usability.md`](output/usability.md), [`output/design.md`](output/design.md), and the screenshot check [`output/app_check.html`](output/app_check.html).

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and put your Portkey key in it (`PORTKEY_PAI_KEY`) (in this folder or the parent folder). `.env` is git-ignored and never committed.

```powershell
cd frontend
npm install
```

## Run the site

Start the API and the front end in two terminals. The API runs from `backend/` with the virtual environment active:

```powershell
.venv\Scripts\Activate.ps1
cd backend
uvicorn main:app --reload --port 8000
```

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173. Test login: `test@campuscustoms.yale.edu` / `password`. Vite proxies `/api` and `/images` to the FastAPI server on port 8000.

### API

- `GET /api/health` — status check
- `GET /api/products` — all products (optional `q`, `category_name`)
- `GET /api/products/{product_id}` — full product with sizes, stock, and photos (product + on-model when available)
- `GET /api/products/{product_id}/related` — similar products for the "You might also like" carousel
- `POST /api/auth/register` — create an account (first/last name, email, password, confirm password)
- `POST /api/auth/login` / `POST /api/auth/logout` / `GET /api/auth/me` — session-cookie login
- `POST /api/chat` — send `{message, history, page}`, get `{reply, results_title, products, answered_by}` (structured product matches the site renders on the Products page)
- `POST /api/chat/stream` — same, but streams fun status lines ("Hunting for Mediums…") as newline-delimited JSON before the reply; used by the chat widget
- `GET /api/chat/history` / `DELETE /api/chat/history` — a logged-in shopper's saved chat (load / clear)
- `GET /api/cart`, `POST /api/cart`, `DELETE /api/cart/{item_id}` — the logged-in shopper's bag
- `GET /images/products/{file}` and `GET /images/on_model/{file}` — product and on-model photos (only these folders are served; the database is not)

## Data (not included in this repo)

The SQLite database and product images are not committed. Place them at:

- `data/campus_customs.db` — `catalogue`, `inventory`, `users`, `chat_messages` tables
- `data/products/*.jpg` — product photos referenced by `catalogue.image_file_path`

Then run `.venv\Scripts\python.exe whiten_backgrounds.py` once to give every photo a white background (originals are kept in `data/products_original/`).

### Optional: AI on-model photos

The product page shows an "On model" photo for any product that has `data/on_model/<product_id>.jpg`. Generate them with the imagegen skill's CLI (gpt-image-2, low quality, ~$0.02 each, ~$1.20 for the 61 products in `imagegen/on_model_products.txt`). This needs an image-enabled `OPENAI_API_KEY`; the course Portkey key only serves chat models.

```bash
while read id; do
  .venv/Scripts/python.exe ../.claude/skills/imagegen/scripts/image_gen.py edit \
    --image "data/products/$id.jpg" --prompt-file imagegen/on_model_prompt.txt --no-augment \
    --model gpt-image-2 --quality low --size 1024x1024 --output-format jpeg --out "data/on_model/$id.jpg"
done < imagegen/on_model_products.txt
```

## Files

- `backend/main.py` — FastAPI app: product, auth, and chat routes, plus product images.
- `backend/agent.py` — the PydanticAI shop agent and its tools; routes each question to gpt-5.6-luna (simple) or gpt-5.6-terra (complex) through Portkey.
- `backend/status.py` — the fun "thinking" messages streamed to the chat while the agent works.
- `backend/tools.py` — catalogue search, product details, stock checks, and related products (used by the routes and the agent).
- `backend/models.py` — Pydantic data types: product cards, stock, chat requests and replies, agent output.
- `backend/prompts/prompt.md` — the agent's system prompt (Campus Customs voice and safety rules).
- `backend/cart.py` — the bag and the confirm-before-adding gate for the assistant's high-impact actions.
- `backend/privacy.py` — removes card numbers, security codes, SSNs, passwords, and phone numbers from chat messages.
- `backend/audit.py` — append-only, hash-chained audit trail in `output/audit_trail.json`.
- `backend/memory.py` — customer memory: saved chat history, customer profile, and past products for logged-in shoppers.
- `backend/auth.py` — accounts: PBKDF2 password hashing, sessions, login rate limit.
- `backend/db.py` — SQLite connection helper.
- `frontend/` — React + Vite + TypeScript site: Home, Products, product pages, About Us, Log in, Create account, and the chat widget.
- `whiten_backgrounds.py` — converts black product-photo backgrounds to white.
- `analyze_database.py` — profiles the database and writes `output/database_overview.html` (interactive charts).
- `output/harness.md` — table and field notes for the shop and chatbot.
- `output/audit_trail.json` — append-only log of agent activity (time, tool, short args/result, reason).
- `output/design.md` — Problem 10 styling changes and why they help.
- `output/app_check.html` + `output/app_check_images/` — Problem 11 screenshot check of the live site.
- `output/usability.md` — Problem 9 usability improvements and how they help customers.
- `imagegen/` — prompt and product list for the optional AI on-model photos.
- `AI_prompts.md` — log of the prompts used to build this project.
