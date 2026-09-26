import { Link } from 'react-router-dom'
import { formatPrice, type ProductSummary } from '../api'

interface Props {
  product: ProductSummary
  /** Why the chat assistant matched this product (shown on chat results). */
  note?: string
  /** Show which sizes are in stock (used for chat results). */
  showSizes?: boolean
}

export default function ProductCard({ product, note, showSizes }: Props) {
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {!product.in_stock && <span className="badge badge-muted">Sold out</span>}
      </div>
      <div className="product-card-body">
        <span className="eyebrow">{product.category}</span>
        <h3>{product.name}</h3>
        <p>{product.short_description}</p>
        {note && <p className="match-note">{note}</p>}
        {showSizes && (
          <p className="card-sizes">
            {product.in_stock ? `In stock: ${product.sizes_in_stock.join(', ')}` : 'Sold out in every size'}
          </p>
        )}
        <div className="product-card-footer">
          <span className="price">{formatPrice(product.price)}</span>
          <span className="swatches" aria-label={`Colors: ${product.colors.join(', ')}`}>
            {product.colors.slice(0, 4).join(' · ')}
          </span>
        </div>
      </div>
    </Link>
  )
}
