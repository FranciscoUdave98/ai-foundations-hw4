import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, formatPrice, getProduct, type ProductDetail, type SizeStock } from '../api'
import { BulldogLoader } from '../components/Brand'
import ProductGallery from '../components/ProductGallery'
import RelatedCarousel from '../components/RelatedCarousel'
import { rememberViewed } from '../pageContext'

function stockLabel(s: SizeStock) {
  if (!s.in_stock) return 'Sold out'
  if (s.low_stock) return `Only ${s.quantity} left`
  return `${s.quantity} in stock`
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  // Results are tagged with the id they belong to, so a new productId shows "Loading" without resetting state.
  const [loaded, setLoaded] = useState<{ id: string; product?: ProductDetail; error?: string }>({ id: '' })
  const [selection, setSelection] = useState({ id: '', size: '' })

  useEffect(() => {
    let cancelled = false
    getProduct(productId)
      .then((product) => {
        if (cancelled) return
        rememberViewed(product.product_id) // page context for the chat: "the one I looked at before"
        setLoaded({ id: productId, product })
      })
      .catch(
        (e: Error) =>
          !cancelled &&
          setLoaded({
            id: productId,
            error: e instanceof ApiError && e.status === 404 ? 'We could not find that product.' : 'Something went wrong loading this product.',
          }),
      )
    return () => {
      cancelled = true
    }
  }, [productId])

  const current = loaded.id === productId ? loaded : { id: productId }
  const product = current.product ?? null
  const error = current.error ?? ''
  const selected = selection.id === productId ? selection.size : ''
  const setSelected = (size: string) => setSelection({ id: productId, size })

  if (error)
    return (
      <div className="container">
        <p className="notice notice-error">{error}</p>
        <Link to="/products" className="link-arrow">
          ← Back to all products
        </Link>
      </div>
    )
  if (!product)
    return (
      <div className="container">
        <BulldogLoader label="Fetching it from the back room…" />
      </div>
    )

  const chosen = product.sizes.find((s) => s.size === selected)

  return (
    <div className="container">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/products">Products</Link>
        <span aria-hidden="true">/</span>
        <Link to={`/products?category=${encodeURIComponent(product.category)}`}>{product.category}</Link>
        <span aria-hidden="true">/</span>
        <span>{product.name}</span>
      </nav>

      <div className="detail">
        <ProductGallery key={product.product_id} images={product.images} />

        <div className="detail-info">
          <span className="eyebrow">{product.category}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>

          <p className="detail-description">{product.description}</p>

          <dl className="detail-facts">
            <div>
              <dt>Style</dt>
              <dd className="cap">{product.garment_type}</dd>
            </div>
            <div>
              <dt>Colors</dt>
              <dd className={product.colors.length ? 'cap' : ''}>{product.colors.length ? product.colors.join(', ') : 'See photo'}</dd>
            </div>
            <div>
              <dt>Availability</dt>
              <dd>
                {product.total_stock > 0
                  ? `${product.total_stock} units across ${product.sizes.filter((s) => s.in_stock).length} of ${product.sizes.length} sizes`
                  : 'Currently sold out'}
              </dd>
            </div>
          </dl>

          <h2 className="detail-subhead">Sizes &amp; stock</h2>
          {product.sizes.length === 0 ? (
            <p className="notice">Size information is not available for this item yet.</p>
          ) : (
            <div className="sizes" role="radiogroup" aria-label="Choose a size">
              {product.sizes.map((s) => (
                <button
                  key={s.size}
                  role="radio"
                  aria-checked={selected === s.size}
                  disabled={!s.in_stock}
                  className={`size ${selected === s.size ? 'active' : ''} ${s.low_stock ? 'low' : ''}`}
                  onClick={() => setSelected(s.size)}
                >
                  <strong>{s.size}</strong>
                  <small>{stockLabel(s)}</small>
                </button>
              ))}
            </div>
          )}
          <p className="size-status" aria-live="polite">
            {chosen
              ? `Size ${chosen.size}: ${stockLabel(chosen).toLowerCase()}. Stop by 57 Broadway or ask our assistant to hold one.`
              : 'Pick a size to check availability.'}
          </p>

          {product.search_tags.length > 0 && (
            <div className="tags">
              {product.search_tags.slice(0, 10).map((t) => (
                <span key={t} className="tag">
                  {t}
                </span>
              ))}
            </div>
          )}

          <Link to="/products" className="link-arrow">
            ← Back to all products
          </Link>
        </div>
      </div>

      <RelatedCarousel productId={product.product_id} />
    </div>
  )
}
