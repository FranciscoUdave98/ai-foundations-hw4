"""Structured data types shared by the API routes, the agent's tools, and the agent's output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# --- Catalogue ---------------------------------------------------------------------------

# How a single (product_id, size) row reads to a shopper. "not_offered" means the size has no
# inventory row at all, which is different from a row with quantity 0 ("sold_out").
StockStatus = Literal["in_stock", "low_stock", "sold_out", "not_offered"]


class SizeStock(BaseModel):
    """One inventory row: exactly one per (product_id, size), enforced by UNIQUE in the database."""

    size: str
    quantity: int
    status: StockStatus
    in_stock: bool
    low_stock: bool


class ProductCard(BaseModel):
    """What the site shows on a product tile, and what the chatbot attaches to a reply."""

    product_id: str
    name: str
    category: str
    garment_type: str
    short_description: str
    colors: list[str]
    price: float
    image_url: str
    in_stock: bool
    sizes_in_stock: list[str] = Field(default_factory=list)


class ProductImage(BaseModel):
    """One photo in the product page gallery."""

    url: str
    kind: Literal["product", "on_model"]
    alt: str


class ProductDetail(ProductCard):
    """Everything on the single-item page."""

    description: str
    search_tags: list[str]
    sizes: list[SizeStock]
    total_stock: int
    images: list[ProductImage] = Field(default_factory=list)


class RelatedProduct(ProductCard):
    """A similar item for the product page carousel, with the reason it's related."""

    reason: str


# --- Agent tool results -------------------------------------------------------------------
# Each tool answers one kind of question, and every result carries the key it was looked up
# by (product_id, and size for stock), so answers can't be mixed up between products.


class ProductMatch(BaseModel):
    """A search hit: enough to identify the product. Price and stock come from their own tools."""

    product_id: str
    name: str
    category: str
    main_color: str | None = Field(description="The garment's own color (fabric). A 'navy hoodie' means main_color is navy.")
    colors: list[str] = Field(description="All colors on the garment: main color first, then print/trim colors.")


class ProductSearchResult(BaseModel):
    """search_products: unique product_ids that match, best first."""

    total_matches: int
    products: list[ProductMatch]
    note: str = ""


class ProductInfo(BaseModel):
    """get_product_info: the description and style facts for one product_id."""

    product_id: str
    name: str
    category: str
    garment_type: str
    description: str
    colors: list[str] = Field(description="Colors that appear on this one colorway (fabric + print), not options.")
    search_tags: list[str]


class PriceQuote(BaseModel):
    """One price per product_id, straight from catalogue.price."""

    product_id: str
    name: str
    price_usd: float


class PriceLookup(BaseModel):
    """get_price: prices for the requested product_ids (duplicates removed)."""

    prices: list[PriceQuote]
    not_found: list[str] = Field(default_factory=list)


class StockLookup(BaseModel):
    """get_stock: inventory for one product_id, for one size or all sizes."""

    product_id: str
    name: str
    requested_size: str | None
    sizes: list[SizeStock]
    total_units: int = Field(description="Units across the sizes listed in `sizes`.")
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    message: str = Field(description="Plain-language summary to relay, e.g. 'Size S is SOLD OUT.'")


class StockLookupResult(BaseModel):
    results: list[StockLookup]
    not_found: list[str] = Field(default_factory=list)


class CatalogueOverview(BaseModel):
    """catalogue_overview: what we sell, category price points, and sizes carried."""

    categories: dict[str, int]
    prices_by_category: dict[str, list[float]]
    sizes: list[str]


# --- Chat ----------------------------------------------------------------------------------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


PageType = Literal["home", "products", "product", "about", "login", "create-account", "other"]


class PageContext(BaseModel):
    """What the shopper is looking at, sent by the browser with every chat message.

    Treated as untrusted: the server validates every id against the catalogue before the
    agent sees it, and free text (the search box) is length-limited and quoted.
    """

    path: str = Field(default="/", max_length=200)
    page_type: PageType = "other"
    product_id: str | None = Field(default=None, max_length=120, description="Product page being viewed.")
    category: str | None = Field(default=None, max_length=40, description="Category filter on the Products page.")
    search: str | None = Field(default=None, max_length=80, description="Text in the Products page search box.")
    shown_product_ids: list[str] = Field(
        default_factory=list, max_length=12, description="Chat-match cards on screen, in on-screen order."
    )
    recently_viewed: list[str] = Field(default_factory=list, max_length=5, description="Product pages viewed this visit, newest first.")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    page: PageContext | None = None


# --- Customer memory (agent tools) --------------------------------------------------------


class CustomerProfile(BaseModel):
    """get_customer_profile: who is chatting. Only ever the logged-in shopper themself."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = None
    saved_messages: int = 0
    last_chat_at: str | None = None


class PastProduct(BaseModel):
    product_id: str
    name: str
    category: str
    last_discussed: str = Field(description="When the assistant last showed this product to the customer (UTC).")
    times_shown: int


class PastProducts(BaseModel):
    """get_past_products: products this customer was shown in earlier chats, most recent first."""

    logged_in: bool
    products: list[PastProduct] = Field(default_factory=list)
    note: str = ""


class PageProduct(BaseModel):
    position: int | None = Field(default=None, description="1-based position on screen, for 'the second one'.")
    product_id: str
    name: str
    category: str


class PageContextInfo(BaseModel):
    """get_page_context: the validated page context, with product names resolved from the database."""

    page_type: PageType
    path: str
    viewing_product: PageProduct | None = None
    category_filter: str | None = None
    search_text: str | None = None
    shown_matches: list[PageProduct] = Field(default_factory=list)
    recently_viewed: list[PageProduct] = Field(default_factory=list)


class CartItem(BaseModel):
    item_id: int
    product_id: str
    name: str
    size: str
    quantity: int
    unit_price: float
    image_url: str


class CartView(BaseModel):
    """The logged-in customer's bag (prices come live from the catalogue)."""

    items: list[CartItem] = Field(default_factory=list)
    item_count: int = 0
    subtotal: float = 0


class PendingAction(BaseModel):
    """A high-impact action the agent proposed; it only happens after the customer explicitly confirms."""

    action_id: str
    summary: str
    status: Literal["awaiting_confirmation", "done", "cancelled", "rejected"]
    message: str = ""


class CartAddRequest(BaseModel):
    """The site's own "Add to bag" button (a click is the customer's explicit consent)."""

    product_id: str = Field(max_length=120)
    size: str = Field(max_length=10)
    quantity: int = Field(default=1, ge=1, le=5)


class RouteDecision(BaseModel):
    """The router's verdict on how hard a chat message is (decides which model answers)."""

    difficulty: Literal["simple", "complex"]
    reason: str = Field(max_length=160, description="One short sentence explaining the choice.")


class ProductMatchRef(BaseModel):
    """One product the agent matched to the shopper's request."""

    product_id: str = Field(description="A product_id returned by a tool this turn.")
    why: str = Field(
        default="",
        max_length=120,
        description="Short reason it matches, e.g. 'Navy, M in stock'. Only facts from tool results.",
    )


class ShopReply(BaseModel):
    """The agent's structured output: the chat text plus the product matches the page should show."""

    reply: str = Field(description="Friendly answer for the shopper, in Campus Customs voice. Markdown allowed.")
    results_title: str | None = Field(
        default=None,
        max_length=80,
        description="Short heading for the matches shown on the page, e.g. 'Gray hoodies in size M'. None if no matches.",
    )
    matches: list[ProductMatchRef] = Field(
        default_factory=list,
        max_length=8,
        description="Products to show on the page as cards, best match first. Empty when no product is relevant.",
    )


class MatchedProduct(ProductCard):
    """A product card built from the database, plus the agent's short reason it matches."""

    match_note: str = ""


class ChatReply(BaseModel):
    """What POST /api/chat returns to the website: the reply and the matches to render on the page."""

    reply: str
    results_title: str | None = None
    products: list[MatchedProduct] = Field(default_factory=list)
    answered_by: Literal["quick", "expert"] | None = Field(default=None, description="Which model tier answered.")


class ChatHistoryMessage(BaseModel):
    """A saved chat message for a logged-in shopper, with the product cards shown alongside it."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    results_title: str | None = None
    products: list[MatchedProduct] = Field(default_factory=list)
    created_at: str
