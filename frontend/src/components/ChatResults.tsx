import { useEffect, useRef } from 'react'
import { useChatResults } from '../useChatResults'
import ProductCard from './ProductCard'

// The live "Matches from your chat" section. It re-renders (and scrolls into view with a
// highlight) every time the assistant returns a new set of product matches.
export default function ChatResults() {
  const { results, clearResults } = useChatResults()
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    if (results) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [results])

  if (!results) return null
  const count = results.products.length

  return (
    <section ref={ref} key={results.updatedAt} className="chat-results" aria-live="polite" aria-label="Matches from your chat">
      <div className="chat-results-head">
        <div>
          <span className="eyebrow">Matches from your chat</span>
          <h2>{results.title}</h2>
          <p>
            {count} {count === 1 ? 'match' : 'matches'} for “{results.query}”
          </p>
        </div>
        <button className="btn btn-outline" onClick={clearResults}>
          Clear matches
        </button>
      </div>
      <div className="product-grid">
        {results.products.map((p) => (
          <ProductCard key={p.product_id} product={p} note={p.match_note} showSizes />
        ))}
      </div>
    </section>
  )
}
