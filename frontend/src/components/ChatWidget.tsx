import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type ReactNode } from 'react'
import { Link, matchPath, useLocation, useNavigate } from 'react-router-dom'
import { clearChatHistory, formatPrice, getChatHistory, sendChatStream, type ChatTurn, type MatchedProduct } from '../api'
import { notifyCartChanged } from '../cartEvents'
import { OPEN_CHAT_EVENT } from '../openChat'
import { buildPageContext } from '../pageContext'
import { useAuth } from '../useAuth'
import { useChatResults } from '../useChatResults'
import { HandsomeDan, PawTrail } from './Brand'

interface Message extends ChatTurn {
  products?: MatchedProduct[]
  title?: string | null
  query?: string // the shopper question this reply answered
}

const HISTORY_TURNS = 12

function welcome(firstName?: string, returning = false): Message {
  const content = returning
    ? `Welcome back, ${firstName}! The Bulldog remembers where we left off. Ask me anything about our crewnecks, hoodies, prices, or sizes.`
    : `Hi${firstName ? ` ${firstName}` : ''}! I'm the Bulldog Assistant 🐾 Ask me about crewnecks, hoodies, prices, or which sizes are in stock.`
  return { role: 'assistant', content }
}

// Minimal, safe Markdown: **bold**, "- " bullet lists, and line breaks. No raw HTML is ever injected.
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  )
}

function renderMarkdown(text: string): ReactNode {
  const blocks: ReactNode[] = []
  let bullets: string[] = []
  const flush = () => {
    if (bullets.length)
      blocks.push(
        <ul key={`ul-${blocks.length}`}>
          {bullets.map((b, i) => (
            <li key={i}>{inline(b)}</li>
          ))}
        </ul>,
      )
    bullets = []
  }
  for (const line of text.split('\n')) {
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/)
    if (bullet) {
      bullets.push(bullet[1])
      continue
    }
    flush()
    if (line.trim()) blocks.push(<p key={`p-${blocks.length}`}>{inline(line)}</p>)
  }
  flush()
  return blocks
}

const PREVIEW = 3

function ChatProducts({ products, onShow }: { products: MatchedProduct[]; onShow: () => void }) {
  return (
    <div className="chat-products">
      {products.slice(0, PREVIEW).map((p) => (
        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
          <img src={p.image_url} alt="" loading="lazy" />
          <span>
            <strong>{p.name}</strong>
            <small>
              {formatPrice(p.price)} · {p.in_stock ? `${p.sizes_in_stock.join(', ')} in stock` : 'Sold out'}
            </small>
          </span>
        </Link>
      ))}
      <button type="button" className="chat-show-page" onClick={onShow}>
        {products.length > PREVIEW ? `See all ${products.length} on the page →` : 'Show on the page →'}
      </button>
    </div>
  )
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { results, showResults } = useChatResults()
  const location = useLocation()
  const navigate = useNavigate()
  const pageProductId = matchPath('/products/:productId', location.pathname)?.params.productId
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>(() => [welcome(user?.first_name)])
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [statusText, setStatusText] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Logged-in shoppers pick up their saved conversation.
  useEffect(() => {
    if (!user) return
    getChatHistory()
      .then((saved) => {
        if (saved.length)
          setMessages([
            welcome(user.first_name, true),
            ...saved.map((m, i) => ({ ...m, title: m.results_title, query: saved[i - 1]?.content })),
          ])
      })
      .catch(() => undefined)
  }, [user])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking, statusText, open])

  // "Ask the Bulldog" buttons elsewhere on the site open the chat (optionally with a question typed in).
  useEffect(() => {
    const onOpen = (e: Event) => {
      setOpen(true)
      const prefill = (e as CustomEvent<{ prefill?: string }>).detail?.prefill
      if (prefill) setDraft(prefill)
    }
    window.addEventListener(OPEN_CHAT_EVENT, onOpen)
    return () => window.removeEventListener(OPEN_CHAT_EVENT, onOpen)
  }, [])

  useEffect(() => {
    if (open) inputRef.current?.focus()
    // Leave room on wide screens so the open chat doesn't cover the product cards.
    document.body.classList.toggle('chat-open', open)
  }, [open])

  // Put a reply's product matches on the page (switching to the Products page if needed).
  function present(m: Message) {
    if (!m.products?.length) return
    showResults({ title: m.title || 'Matching products', query: m.query ?? '', products: m.products })
    if (location.pathname !== '/products') navigate('/products')
  }

  async function send(e?: FormEvent) {
    e?.preventDefault()
    const text = draft.trim()
    if (!text || thinking) return
    // Guests send the conversation so far (minus the greeting); the server keeps it for logged-in users.
    const history = messages.slice(1).slice(-HISTORY_TURNS).map(({ role, content }) => ({ role, content }))
    setDraft('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setThinking(true)
    try {
      const page = buildPageContext(location, results)
      const { reply, products, results_title } = await sendChatStream(text, history, page, setStatusText)
      const answer: Message = { role: 'assistant', content: reply, products, title: results_title, query: text }
      setMessages((m) => [...m, answer])
      notifyCartChanged() // the Bulldog may have added a confirmed item to the bag
      // A question about the product on screen ("is this in XL?") shouldn't navigate away from it.
      const onlyThisPage = products.length === 1 && products[0].product_id === pageProductId
      if (products.length && !onlyThisPage) present(answer)
    } catch (err) {
      const content = err instanceof Error ? err.message : "Sorry, I couldn't reach the shop right now. Please try again."
      setMessages((m) => [...m, { role: 'assistant', content }])
    } finally {
      setThinking(false)
      setStatusText('')
    }
  }

  // Logged in: delete the saved history on the server. Guests: just reset this browser's chat.
  async function clearChat() {
    if (user) {
      if (!window.confirm('Delete your saved chat history? This cannot be undone.')) return
      try {
        await clearChatHistory()
      } catch {
        return
      }
    }
    setMessages([welcome(user?.first_name)])
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send()
    }
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Bulldog Assistant chat">
          <header className="chat-header">
            <span className="chat-avatar" aria-hidden="true">
              <HandsomeDan size={34} />
            </span>
            <div className="chat-title">
              <strong>Bulldog Assistant</strong>
              <small>{user ? `Signed in as ${user.first_name} · chat is saved` : 'Guest · log in to save this chat'}</small>
            </div>
            <div className="chat-header-actions">
              {messages.length > 1 && (
                <button className="chat-clear" onClick={clearChat} title={user ? 'Delete saved chat history' : 'Start over'}>
                  {user ? 'Clear history' : 'Start over'}
                </button>
              )}
              <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>
          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className={`chat-turn chat-turn-${m.role}`}>
                {m.role === 'assistant' ? (
                  <div className="assistant-row">
                    <span className="bubble-avatar" aria-hidden="true">
                      <HandsomeDan size={24} />
                    </span>
                    <div className="bubble bubble-assistant">{renderMarkdown(m.content)}</div>
                  </div>
                ) : (
                  <div className="bubble bubble-user">{m.content}</div>
                )}
                {m.products && m.products.length > 0 && <ChatProducts products={m.products} onShow={() => present(m)} />}
              </div>
            ))}
            {thinking && (
              <div className="thinking" role="status" aria-live="polite">
                {/* Handsome Dan sniffing around while the agent works */}
                <span className="thinking-dan" aria-hidden="true">
                  <HandsomeDan size={46} className="dan-thinking" />
                </span>
                <span className="thinking-body">
                  <span key={statusText} className="status-text">
                    {statusText || 'The Bulldog is on it…'}
                  </span>
                  <PawTrail count={4} className="thinking-paws" />
                </span>
              </div>
            )}
          </div>
          <form className="chat-input" onSubmit={send}>
            <textarea
              ref={inputRef}
              rows={1}
              value={draft}
              maxLength={1000}
              placeholder="Ask the Bulldog about a hoodie, size, or price…"
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
            />
            <button type="submit" disabled={!draft.trim() || thinking}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className="chat-launcher"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={open ? 'Close chat' : 'Ask the Bulldog Assistant'}
      >
        {open ? '×' : (
          <>
            <span className="launcher-dan" aria-hidden="true">
              <HandsomeDan size={34} />
            </span>
            <span>Ask the Bulldog</span>
          </>
        )}
      </button>
    </div>
  )
}
