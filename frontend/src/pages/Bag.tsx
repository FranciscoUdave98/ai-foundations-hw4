import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, getCart, removeCartItem, type CartView } from '../api'
import { BulldogLoader, HandsomeDan } from '../components/Brand'
import { notifyCartChanged } from '../cartEvents'
import { openChat } from '../openChat'
import { useAuth } from '../useAuth'

export default function Bag() {
  const { user } = useAuth()
  const [cart, setCart] = useState<CartView | null>(null)

  useEffect(() => {
    getCart().then(setCart).catch(() => setCart({ items: [], item_count: 0, subtotal: 0 }))
  }, [user])

  async function remove(itemId: number) {
    setCart(await removeCartItem(itemId))
    notifyCartChanged()
  }

  if (!user)
    return (
      <div className="container not-found">
        <HandsomeDan size={110} />
        <h1>Your bag</h1>
        <p>Log in to keep a bag. The Bulldog Assistant can add items for you, but only after you confirm.</p>
        <Link to="/login" className="btn btn-primary">
          Log in
        </Link>
      </div>
    )
  if (!cart) return <BulldogLoader label="Opening your bag…" />

  return (
    <div className="container bag">
      <div className="page-head">
        <h1>Your bag</h1>
        <p>Items are only added when you click "Add" or confirm with the Bulldog Assistant. Checkout happens in store at 57 Broadway.</p>
      </div>
      {cart.items.length === 0 ? (
        <div className="notice">
          Your bag is empty. <button className="link-button" onClick={() => openChat('Help me find something for my bag')}>Ask the Bulldog</button> or{' '}
          <Link to="/products">browse products</Link>.
        </div>
      ) : (
        <>
          <ul className="bag-list">
            {cart.items.map((i) => (
              <li key={i.item_id} className="bag-item">
                <img src={i.image_url} alt="" />
                <div>
                  <Link to={`/products/${i.product_id}`}>
                    <strong>{i.name}</strong>
                  </Link>
                  <span>
                    Size {i.size} · Qty {i.quantity} · {formatPrice(i.unit_price)} each
                  </span>
                </div>
                <span className="price">{formatPrice(i.unit_price * i.quantity)}</span>
                <button className="btn btn-outline" onClick={() => remove(i.item_id)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
          <p className="bag-total">
            {cart.item_count} {cart.item_count === 1 ? 'item' : 'items'} · Subtotal <span className="price">{formatPrice(cart.subtotal)}</span>
          </p>
        </>
      )}
    </div>
  )
}
