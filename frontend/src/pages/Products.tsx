import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CATEGORIES, getProducts, type ProductSummary } from '../api'
import { BulldogLoader } from '../components/Brand'
import ChatResults from '../components/ChatResults'
import ProductCard from '../components/ProductCard'

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState('')
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const query = params.get('q') ?? ''

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch(() => setError('We could not load the catalogue. Is the backend running?'))
  }, [])

  const visible = useMemo(() => {
    if (!products) return []
    const needle = query.trim().toLowerCase()
    return products.filter(
      (p) =>
        (!category || p.category === category) &&
        (!needle || [p.name, p.short_description, p.category, ...p.colors].join(' ').toLowerCase().includes(needle)),
    )
  }, [products, category, query])

  function update(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  return (
    <div className="container">
      <div className="page-head">
        <h1>Shop Yale apparel</h1>
        <p>Every crewneck, hoodie, and tee we carry, with prices and sizes in stock.</p>
      </div>

      <ChatResults />

      <div className="filters">
        <input
          type="search"
          className="search"
          placeholder="Search by name, color, or college…"
          value={query}
          onChange={(e) => update('q', e.target.value)}
          aria-label="Search products"
        />
        <div className="chips" role="group" aria-label="Filter by category">
          <button className={`chip ${!category ? 'active' : ''}`} onClick={() => update('category', '')}>
            All
          </button>
          {CATEGORIES.map((c) => (
            <button key={c} className={`chip ${category === c ? 'active' : ''}`} onClick={() => update('category', c)}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="notice notice-error">{error}</p>}
      {!products && !error && <BulldogLoader label="Sniffing out every hoodie and tee…" />}
      {products && (
        <p className="result-count">
          {visible.length} {visible.length === 1 ? 'product' : 'products'}
        </p>
      )}
      <div className="product-grid">
        {visible.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
      {products && visible.length === 0 && (
        <p className="notice">No products match that search. Try another color or style.</p>
      )}
    </div>
  )
}
