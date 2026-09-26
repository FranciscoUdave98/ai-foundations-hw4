/** Tell the nav bar's bag count to refresh (after a chat reply or a bag change). */
export const CART_CHANGED_EVENT = 'cc:cart-changed'

export function notifyCartChanged() {
  window.dispatchEvent(new Event(CART_CHANGED_EVENT))
}
