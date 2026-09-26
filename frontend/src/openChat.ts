/** Ask the chat widget to open (used by "Ask the Bulldog" buttons outside the widget). */
export const OPEN_CHAT_EVENT = 'cc:open-chat'

export function openChat(prefill?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_CHAT_EVENT, { detail: { prefill } }))
}
