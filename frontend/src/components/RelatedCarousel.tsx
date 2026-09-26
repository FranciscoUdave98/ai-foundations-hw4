import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, getRelated, type RelatedProduct } from '../api'

/** "You might also like": a swipeable row of similar products under the product page. */
export default function RelatedCarousel({ productId }: { productId: string }) {
  const [items, setItems] = useState<RelatedProduct[]>([])
  const [edges, setEdges] = useState({ start: true, end: false })
  const track = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    getRelated(productId, 12)
      .then((r) => !cancelled && setItems(r))
      .catch(() => !cancelled && setItems([]))
    return () => {
      cancelled = true
    }
  }, [productId])

  const updateEdges = useCallback(() => {
    const el = track.current
    if (!el) return
    setEdges({ start: el.scrollLeft <= 4, end: el.scrollLeft + el.clientWidth >= el.scrollWidth - 4 })
  }, [])

  useEffect(() => {
    const el = track.current
    if (!el) return
    el.scrollTo({ left: 0 })
    updateEdges()
    const ro = new ResizeObserver(updateEdges)
    ro.observe(el)
    return () => ro.disconnect()
  }, [items, updateEdges])

  function scrollBy(dir: 1 | -1) {
    const el = track.current
    if (el) el.scrollBy({ left: dir * el.clientWidth * 0.85, behavior: 'smooth' })
  }

  if (items.length === 0) return null

  return (
    <section className="related" aria-label="Related products">
      <div className="related-head">
        <div>
          <h2>You might also like</h2>
          <p>Similar styles, colleges, and colors</p>
        </div>
        <div className="related-controls">
          <button onClick={() => scrollBy(-1)} disabled={edges.start} aria-label="Previous related products">
            ‹
          </button>
          <button onClick={() => scrollBy(1)} disabled={edges.end} aria-label="Next related products">
            ›
          </button>
        </div>
      </div>
      <div className="related-track" ref={track} onScroll={updateEdges}>
        {items.map((p) => (
          <Link key={p.product_id} to={`/products/${p.product_id}`} className="related-card">
            <div className="related-image">
              <img src={p.image_url} alt={p.name} loading="lazy" />
              {!p.in_stock && <span className="badge badge-muted">Sold out</span>}
            </div>
            <span className="related-reason">{p.reason}</span>
            <strong>{p.name}</strong>
            <span className="price">{formatPrice(p.price)}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}
