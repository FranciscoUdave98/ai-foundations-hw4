"""Catalogue and stock lookups used by both the API routes and the shop agent's tools.

Everything reads live from data/campus_customs.db, so prices and stock are always current.
Each agent lookup answers one kind of question from one table:
    search_products  -> which product_ids match      (catalogue)
    get_product_info -> description and style facts (catalogue, by product_id)
    get_prices       -> price                        (catalogue.price, by product_id)
    get_stock        -> quantity per size            (inventory, by product_id + size)
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict

from db import DATA_DIR, connect
from models import (
    CatalogueOverview,
    PriceLookup,
    PriceQuote,
    ProductCard,
    ProductDetail,
    ProductImage,
    ProductInfo,
    ProductMatch,
    ProductSearchResult,
    RelatedProduct,
    SizeStock,
    StockLookup,
    StockLookupResult,
    StockStatus,
)

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 5
ON_MODEL_DIR = DATA_DIR / "on_model"  # AI-generated on-model photos, <product_id>.jpg (optional)
CATEGORIES = ["Crewnecks", "Hoodies", "T-shirts", "Quarter-zips", "Jackets & fleece", "Long-sleeve"]

# --- Display clean-up ---------------------------------------------------------------------


def category(garment_type: str) -> str:
    """Collapse the 22 free-text garment_type labels into shop categories."""
    g = garment_type.lower()
    if "t-shirt" in g:
        return "T-shirts"
    if "quarter-zip" in g:
        return "Quarter-zips"
    if "jacket" in g:
        return "Jackets & fleece"
    if "hood" in g:
        return "Hoodies"
    if "crew" in g:
        return "Crewnecks"
    return "Long-sleeve"


_NAME_FIXES = [
    (r"\b1 4 Zip\b", "1/4 Zip"),
    (r"\bT Shirt\b", "T-Shirt"),
    (r"\bL S 2 0\b", "L/S 2.0"),
    (r"^Ua\b", "UA"),
    (r"\bVs\b", "vs."),
    (r"\bAnd\b", "and"),
    (r"\bOf\b", "of"),
    (r"\bCreqneck\b", "Crewneck"),
    (r"\bMens\b", "Men's"),
    (r"\bTrack Field\b", "Track & Field"),
    (r"\bVit\b", "VIT"),
    (r" 1$", ""),
]


def display_name(name: str) -> str:
    """Tidy names generated from file slugs, e.g. 'Morse 1 4 Zip' -> 'Morse 1/4 Zip'."""
    for pattern, repl in _NAME_FIXES:
        name = re.sub(pattern, repl, name)
    return name


def description(row: sqlite3.Row) -> str:
    """Replace the three catalogue stubs (image analysis was blocked) with shopper-friendly copy."""
    text = row["description"]
    if "filename-based stub" in text:
        return (
            f"The {display_name(row['name'])} is a Campus Customs {row['garment_type'].lower()}. "
            "See the photo for the full design and colors."
        )
    return text


def short_description(text: str, limit: int = 110) -> str:
    first = text.split(". ")[0].rstrip(".") + "."
    if len(first) <= limit:
        return first
    return first[:limit].rsplit(" ", 1)[0].rstrip(",;") + "…"


# --- Stock status ---------------------------------------------------------------------------

_SIZE_WORDS = {
    "EXTRA SMALL": "XS", "X-SMALL": "XS", "SMALL": "S", "MEDIUM": "M", "MED": "M", "LARGE": "L",
    "EXTRA LARGE": "XL", "X-LARGE": "XL", "XX-LARGE": "XXL", "2XL": "XXL", "2X": "XXL",
}


def normalize_size(size: str) -> str:
    s = size.upper().strip()
    return _SIZE_WORDS.get(s, s)


def stock_status(quantity: int | None) -> StockStatus:
    """None = the size has no inventory row; 0 = sold out; 1-5 = low stock."""
    if quantity is None:
        return "not_offered"
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK else "in_stock"


def _size_stock(size: str, quantity: int | None) -> SizeStock:
    status = stock_status(quantity)
    return SizeStock(
        size=size,
        quantity=max(quantity or 0, 0),
        status=status,
        in_stock=status in ("in_stock", "low_stock"),
        low_stock=status == "low_stock",
    )


def _unique(values: list[str]) -> list[str]:
    """Drop repeats but keep order, so each key is looked up (and answered) exactly once."""
    seen: dict[str, None] = {}
    for v in values:
        if v and v.strip():
            seen.setdefault(v.strip(), None)
    return list(seen)


# --- Loading --------------------------------------------------------------------------------


def _catalogue_row(conn: sqlite3.Connection, product_id: str) -> sqlite3.Row | None:
    # product_id is the catalogue PRIMARY KEY, so this returns at most one row.
    return conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id.strip(),)).fetchone()


def _inventory(conn: sqlite3.Connection, product_id: str) -> dict[str, int]:
    # UNIQUE (product_id, size) guarantees one quantity per size.
    return dict(conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall())


def _stock_by_product(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    stock: dict[str, dict[str, int]] = defaultdict(dict)
    for pid, size, qty in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        stock[pid][size] = qty
    return stock


def _card(row: sqlite3.Row, stock: dict[str, int]) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=display_name(row["name"]),
        category=category(row["garment_type"]),
        garment_type=row["garment_type"],
        short_description=short_description(description(row)),
        colors=json.loads(row["colors"]),
        price=row["price"],
        image_url=f"/images/{row['image_file_path']}",
        in_stock=any(q > 0 for q in stock.values()),
        sizes_in_stock=[s for s in SIZES if stock.get(s, 0) > 0],
    )


def _load() -> tuple[list[sqlite3.Row], dict[str, dict[str, int]]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        return rows, _stock_by_product(conn)


def list_product_cards() -> list[ProductCard]:
    rows, stock = _load()
    return [_card(r, stock[r["product_id"]]) for r in rows]


def get_product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Cards for known ids, in the order given; repeats and unknown ids are dropped (nothing is invented)."""
    rows, stock = _load()
    by_id = {r["product_id"]: r for r in rows}
    return [_card(by_id[pid], stock[pid]) for pid in _unique(product_ids) if pid in by_id]


def get_product_detail(product_id: str) -> ProductDetail | None:
    with connect() as conn:
        row = _catalogue_row(conn, product_id)
        if row is None:
            return None
        stock = _inventory(conn, row["product_id"])
    sizes = [_size_stock(s, stock[s]) for s in SIZES if s in stock]
    card = _card(row, stock)
    return ProductDetail(
        **card.model_dump(),
        description=description(row),
        search_tags=json.loads(row["search_tags"]),
        sizes=sizes,
        total_stock=sum(s.quantity for s in sizes),
        images=product_images(card),
    )


def product_images(card: ProductCard) -> list[ProductImage]:
    """The catalogue photo, plus an on-model photo when one has been generated for this product."""
    images = [ProductImage(url=card.image_url, kind="product", alt=card.name)]
    if (ON_MODEL_DIR / f"{card.product_id}.jpg").exists():
        images.append(
            ProductImage(url=f"/images/on_model/{card.product_id}.jpg", kind="on_model", alt=f"{card.name}, worn by a model")
        )
    return images


# --- Related products (product page carousel) ----------------------------------------------

_GENERIC_NAME_WORDS = {
    "yale", "hoodie", "hood", "crewneck", "crew", "t", "shirt", "tee", "1", "4", "zip", "left", "chest", "sports",
    "sport", "big", "basic", "logo", "college", "school", "of", "the", "and", "vs", "fleece", "jacket", "sweater",
    "full", "double", "knit", "heavyweight", "tri", "blend", "long", "sleeve", "mens", "ua", "2", "0", "l", "s",
    "university", "premium", "vintage", "district", "vit", "champion", "reverse", "weave", "arched", "crest",
}


def _name_themes(name: str) -> set[str]:
    """Distinctive words in a product name: the college, sport, or family word ('saybrook', 'dad', 'hockey')."""
    return {w for w in re.findall(r"[a-z]+", name.lower()) if w not in _GENERIC_NAME_WORDS and len(w) > 2}


def related_products(product_id: str, limit: int = 10) -> list[RelatedProduct]:
    """Similar items for the product page: same college/sport/family theme, style, color, and price."""
    rows, stock = _load()
    by_id = {r["product_id"]: r for r in rows}
    base = by_id.get(product_id)
    if base is None:
        return []
    tag_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        for t in {t.lower() for t in json.loads(r["search_tags"])}:
            tag_counts[t] += 1
    rare = {t for t, n in tag_counts.items() if n <= 12}  # tags on most products (e.g. "yale") say nothing

    base_card = _card(base, stock[product_id])
    base_themes = _name_themes(base_card.name)
    base_tags = {t.lower() for t in json.loads(base["search_tags"])} & rare
    base_color = (base_card.colors[:1] or [""])[0].lower()

    scored: list[tuple[float, str, ProductCard]] = []
    for r in rows:
        if r["product_id"] == product_id:
            continue
        card = _card(r, stock[r["product_id"]])
        themes = base_themes & _name_themes(card.name)
        shared_tags = base_tags & {t.lower() for t in json.loads(r["search_tags"])}
        same_color = bool(base_color) and (card.colors[:1] or [""])[0].lower() == base_color
        # A shared theme (college, sport, family word) counts most; multi-word themes like 'Benjamin Franklin' count once.
        score = (8.0 + len(themes) - 1 if themes else 0) + 1.0 * len(shared_tags) + (3.0 if card.category == base_card.category else 0)
        score += 1.5 if same_color else 0
        score += 1.0 if abs(card.price - base_card.price) <= 15 else 0
        score -= 5.0 if not card.in_stock else 0
        if themes:
            reason = f"Also {' '.join(w.title() for w in sorted(themes))}"
        elif card.category == base_card.category and same_color:
            reason = "Same style & color"
        elif card.category == base_card.category:
            reason = "Same style"
        elif same_color:
            reason = "Same color"
        else:
            reason = "Shoppers also like"
        scored.append((score, reason, card))

    scored.sort(key=lambda x: (-x[0], x[2].name))
    return [RelatedProduct(**card.model_dump(), reason=reason) for _, reason, card in scored[: max(1, min(limit, 16))]]


# --- Search -------------------------------------------------------------------------------

_STOPWORDS = {
    "a", "an", "and", "any", "are", "do", "for", "have", "i", "in", "is", "it", "me", "my", "of", "on",
    "or", "show", "some", "something", "that", "the", "this", "to", "want", "with", "you", "your",
    "yale", "campus", "customs", "merch", "looking", "find", "get", "need", "like", "would",
}
_SYNONYMS = {"tee": "shirt", "tshirt": "shirt", "hood": "hoodie", "quarterzip": "quarter"}
_CATEGORY_WORDS = {
    "crewneck": "Crewnecks", "crew": "Crewnecks", "hoodie": "Hoodies", "shirt": "T-shirts",
    "quarter": "Quarter-zips", "jacket": "Jackets & fleece", "fleece": "Jackets & fleece",
}


def _terms(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in _STOPWORDS or len(w) < 2:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # hoodies -> hoodie, shirts -> shirt
        out.append(_SYNONYMS.get(w, w))
    return out


def _normalize_color(c: str) -> str:
    c = c.lower().strip()
    return "navy" if c in ("navy blue", "dark blue") else ("gray" if c == "grey" else c)


def search_cards(
    query: str | None = None,
    category_name: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = False,
    color_anywhere: bool = False,
) -> list[ProductCard]:
    """Keyword search over names, tags, descriptions, and colors, plus filters. One card per product_id.

    `color` matches the garment's main color (the first entry in `colors`) unless `color_anywhere`
    is set, in which case print/trim colors count too ("navy lettering").
    """
    rows, stock = _load()
    terms = _terms(query or "")
    wanted_size = normalize_size(size) if size else None
    wanted_color = _normalize_color(color) if color else None
    if category_name and category_name not in CATEGORIES:
        category_name = next((c for c in CATEGORIES if c.lower().startswith(category_name.lower()[:4])), None)

    scored: list[tuple[int, ProductCard]] = []
    for r in rows:  # catalogue rows are unique by product_id, so no product can appear twice
        card = _card(r, stock[r["product_id"]])
        if category_name and card.category != category_name:
            continue
        if max_price is not None and card.price > max_price:
            continue
        if min_price is not None and card.price < min_price:
            continue
        if wanted_color:
            pool = card.colors if color_anywhere else card.colors[:1]
            if not any(wanted_color in _normalize_color(c) for c in pool):
                continue
        if wanted_size and wanted_size not in card.sizes_in_stock:
            continue
        if in_stock_only and not card.in_stock:
            continue
        score = 0
        if terms:
            fields = [
                (display_name(r["name"]).lower(), 3),
                (" ".join(json.loads(r["search_tags"])).lower(), 2),
                (f"{card.category} {r['garment_type']}".lower(), 2),
                (" ".join(card.colors).lower(), 2),
                (description(r).lower(), 1),
            ]
            for term in terms:
                score += sum(weight for text, weight in fields if term in text)
                if _CATEGORY_WORDS.get(term) == card.category:
                    score += 2
            if score == 0:
                continue
        scored.append((score, card))

    scored.sort(key=lambda sc: (-sc[0], not sc[1].in_stock, sc[1].name))
    return [c for _, c in scored]


# --- Agent lookups (one tool per fact) ------------------------------------------------------


def search_products(
    query: str | None = None,
    category_name: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = False,
    limit: int = 8,
    color_anywhere: bool = False,
) -> ProductSearchResult:
    """Find product_ids. Deliberately returns no price or quantity: those come from get_prices / get_stock."""
    cards = search_cards(query, category_name, color, max_price, min_price, size, in_stock_only, color_anywhere)
    matches = [
        ProductMatch(
            product_id=c.product_id,
            name=c.name,
            category=c.category,
            main_color=c.colors[0] if c.colors else None,
            colors=c.colors,
        )
        for c in cards
    ]
    note = "" if matches else "No products matched. Try fewer words, another color, or a broader category."
    return ProductSearchResult(total_matches=len(matches), products=matches[: max(1, limit)], note=note)


def get_product_info(product_id: str) -> ProductInfo | None:
    """Description and style facts for one product (catalogue row, by primary key)."""
    with connect() as conn:
        row = _catalogue_row(conn, product_id)
    if row is None:
        return None
    return ProductInfo(
        product_id=row["product_id"],
        name=display_name(row["name"]),
        category=category(row["garment_type"]),
        garment_type=row["garment_type"],
        description=description(row),
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
    )


def get_prices(product_ids: list[str]) -> PriceLookup:
    """catalogue.price for each unique product_id; unknown ids are reported, never guessed."""
    quotes: list[PriceQuote] = []
    missing: list[str] = []
    with connect() as conn:
        for pid in _unique(product_ids):
            row = _catalogue_row(conn, pid)
            if row is None:
                missing.append(pid)
            else:
                quotes.append(PriceQuote(product_id=row["product_id"], name=display_name(row["name"]), price_usd=row["price"]))
    return PriceLookup(prices=quotes, not_found=missing)


def _stock_message(name: str, sizes: list[SizeStock], requested: str | None) -> str:
    if requested:
        s = sizes[0]
        return {
            "in_stock": f"{name}: size {s.size} is IN STOCK ({s.quantity} available).",
            "low_stock": f"{name}: size {s.size} is LOW STOCK (only {s.quantity} left).",
            "sold_out": f"{name}: size {s.size} is SOLD OUT (0 available).",
            "not_offered": f"{name}: size {s.size} is NOT OFFERED for this product.",
        }[s.status]
    if not any(s.in_stock for s in sizes):
        return f"{name} is SOLD OUT in every size."
    sold_out = [s.size for s in sizes if s.status == "sold_out"]
    in_stock = [s.size for s in sizes if s.in_stock]
    msg = f"{name}: in stock in {', '.join(in_stock)}."
    return msg + (f" SOLD OUT in {', '.join(sold_out)}." if sold_out else "")


def get_stock(product_ids: list[str], size: str | None = None) -> StockLookupResult:
    """inventory.quantity for each unique product_id: one size, or every size."""
    requested = normalize_size(size) if size else None
    results: list[StockLookup] = []
    missing: list[str] = []
    with connect() as conn:
        for pid in _unique(product_ids):
            row = _catalogue_row(conn, pid)
            if row is None:
                missing.append(pid)
                continue
            stock = _inventory(conn, row["product_id"])
            if requested:
                sizes = [_size_stock(requested, stock.get(requested))]
            else:
                sizes = [_size_stock(s, stock[s]) for s in SIZES if s in stock]
            name = display_name(row["name"])
            results.append(
                StockLookup(
                    product_id=row["product_id"],
                    name=name,
                    requested_size=requested,
                    sizes=sizes,
                    total_units=sum(s.quantity for s in sizes),
                    sizes_in_stock=[s for s in SIZES if stock.get(s, 0) > 0],
                    sold_out_sizes=[s for s in SIZES if s in stock and stock[s] <= 0],
                    message=_stock_message(name, sizes, requested),
                )
            )
    return StockLookupResult(results=results, not_found=missing)


def catalogue_overview() -> CatalogueOverview:
    cards = list_product_cards()
    counts: dict[str, int] = {c: 0 for c in CATEGORIES}
    prices: dict[str, set[float]] = defaultdict(set)
    for c in cards:
        counts[c.category] += 1
        prices[c.category].add(c.price)
    return CatalogueOverview(
        categories=counts,
        prices_by_category={c: sorted(prices[c]) for c in CATEGORIES},
        sizes=SIZES,
    )
