export interface ProductSummary {
  product_id: string
  name: string
  category: string
  garment_type: string
  short_description: string
  colors: string[]
  price: number
  image_url: string
  in_stock: boolean
  sizes_in_stock: string[]
}

export interface SizeStock {
  size: string
  quantity: number
  status: 'in_stock' | 'low_stock' | 'sold_out' | 'not_offered'
  in_stock: boolean
  low_stock: boolean
}

export interface ProductImage {
  url: string
  kind: 'product' | 'on_model'
  alt: string
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  sizes: SizeStock[]
  total_stock: number
  images: ProductImage[]
}

export interface RelatedProduct extends ProductSummary {
  reason: string
}

export interface MatchedProduct extends ProductSummary {
  match_note: string
}

export interface ChatReply {
  reply: string
  results_title: string | null
  products: MatchedProduct[]
  answered_by?: 'quick' | 'expert' | null
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatHistoryMessage extends ChatTurn {
  results_title: string | null
  products: MatchedProduct[]
  created_at: string
}

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  created_at: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI sends {detail: "text"} for our errors and {detail: [{msg}]} for validation errors.
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, '')
  return `Request failed (${status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { credentials: 'same-origin', ...init })
  if (!res.ok) throw new ApiError(res.status, errorMessage(await res.json().catch(() => null), res.status))
  return (res.status === 204 ? undefined : await res.json()) as T
}

const postJson = <T>(path: string, body: unknown) =>
  request<T>(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const getProducts = () => request<ProductSummary[]>('/api/products')

export const getProduct = (id: string) => request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export type PageType = 'home' | 'products' | 'product' | 'about' | 'login' | 'create-account' | 'other'

/** What the shopper is looking at, sent with every chat message (validated by the server). */
export interface PageContext {
  path: string
  page_type: PageType
  product_id: string | null
  category: string | null
  search: string | null
  shown_product_ids: string[]
  recently_viewed: string[]
}

export const sendChat = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatReply>('/api/chat', { message, history, page })

/**
 * Streaming chat: calls onStatus with each "thinking" line the agent sends
 * ("Hunting for Mediums…"), then resolves with the final reply.
 */
export async function sendChatStream(
  message: string,
  history: ChatTurn[],
  page: PageContext,
  onStatus: (text: string) => void,
): Promise<ChatReply> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })
  if (!res.ok || !res.body) throw new ApiError(res.status, errorMessage(await res.json().catch(() => null), res.status))
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
    let newline: number
    while ((newline = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, newline).trim()
      buffer = buffer.slice(newline + 1)
      if (!line) continue
      const event = JSON.parse(line) as { type: string; text?: string; detail?: string } & ChatReply
      if (event.type === 'status' && event.text) onStatus(event.text)
      else if (event.type === 'reply') return event
      else if (event.type === 'error') throw new ApiError(503, event.detail ?? 'Something went wrong.')
    }
    if (done) throw new ApiError(503, 'The answer was cut off. Please try again.')
  }
}

export const getRelated = (id: string, limit = 10) =>
  request<RelatedProduct[]>(`/api/products/${encodeURIComponent(id)}/related?limit=${limit}`)

export interface CartItem {
  item_id: number
  product_id: string
  name: string
  size: string
  quantity: number
  unit_price: number
  image_url: string
}

export interface CartView {
  items: CartItem[]
  item_count: number
  subtotal: number
}

export const getCart = () => request<CartView>('/api/cart')

export const addCartItem = (product_id: string, size: string, quantity = 1) =>
  postJson<CartView>('/api/cart', { product_id, size, quantity })

export const removeCartItem = (itemId: number) => request<CartView>(`/api/cart/${itemId}`, { method: 'DELETE' })

export const getChatHistory = () => request<ChatHistoryMessage[]>('/api/chat/history')

export const clearChatHistory = () => request<{ deleted: number }>('/api/chat/history', { method: 'DELETE' })

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

export const register = (input: RegisterInput) => postJson<User>('/api/auth/register', input)

export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })

export const logout = () => postJson<void>('/api/auth/logout', {})

export const getMe = () => request<User>('/api/auth/me')

export const formatPrice = (price: number) => `$${price.toFixed(price % 1 ? 2 : 0)}`

export const CATEGORIES = ['Crewnecks', 'Hoodies', 'T-shirts', 'Quarter-zips', 'Jackets & fleece', 'Long-sleeve']
