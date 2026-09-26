import { matchPath, type Location } from 'react-router-dom'
import type { PageContext, PageType } from './api'
import type { ChatResults } from './useChatResults'

const RECENT_KEY = 'cc_recently_viewed'
const RECENT_MAX = 5

/** Remember product pages viewed this visit (sessionStorage: cleared when the tab closes). */
export function rememberViewed(productId: string) {
  try {
    const list = JSON.parse(sessionStorage.getItem(RECENT_KEY) ?? '[]') as string[]
    const next = [productId, ...list.filter((id) => id !== productId)].slice(0, RECENT_MAX)
    sessionStorage.setItem(RECENT_KEY, JSON.stringify(next))
  } catch {
    // Storage can be unavailable (private mode); page context just won't include history.
  }
}

function recentlyViewed(): string[] {
  try {
    return (JSON.parse(sessionStorage.getItem(RECENT_KEY) ?? '[]') as string[]).slice(0, RECENT_MAX)
  } catch {
    return []
  }
}

const PAGE_TYPES: Record<string, PageType> = {
  '/': 'home',
  '/products': 'products',
  '/about': 'about',
  '/login': 'login',
  '/create-account': 'create-account',
}

/** Build the page context from the current URL, the Products page filters, and the chat matches on screen. */
export function buildPageContext(location: Location, results: ChatResults | null): PageContext {
  const productId = matchPath('/products/:productId', location.pathname)?.params.productId ?? null
  const pageType: PageType = productId ? 'product' : (PAGE_TYPES[location.pathname] ?? 'other')
  const params = new URLSearchParams(location.search)
  const onProducts = pageType === 'products'
  return {
    path: location.pathname + location.search,
    page_type: pageType,
    product_id: productId,
    category: onProducts ? params.get('category') : null,
    search: onProducts ? params.get('q') : null,
    // Chat matches are only on screen on the Products page.
    shown_product_ids: onProducts && results ? results.products.map((p) => p.product_id) : [],
    recently_viewed: recentlyViewed(),
  }
}
