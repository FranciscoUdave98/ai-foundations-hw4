import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { getCart } from '../api'
import { CART_CHANGED_EVENT } from '../cartEvents'
import { useAuth } from '../useAuth'
import { HandsomeDan } from './Brand'

const TABS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const [bagCount, setBagCount] = useState(0)

  // Bag count: refreshed on login/logout and whenever the chat or the Bag page changes the bag.
  useEffect(() => {
    const refresh = () => {
      getCart()
        .then((c) => setBagCount(c.item_count))
        .catch(() => setBagCount(0))
    }
    refresh()
    window.addEventListener(CART_CHANGED_EVENT, refresh)
    return () => window.removeEventListener(CART_CHANGED_EVENT, refresh)
  }, [user])
  const close = () => setOpen(false)

  async function onLogout() {
    close()
    await logout()
    navigate('/')
  }

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand" aria-label="Campus Customs home" onClick={close}>
          <span className="brand-mark">
            <HandsomeDan size={38} />
          </span>
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <small>New Haven · Est. 1975</small>
          </span>
        </Link>
        <button
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="nav-tabs"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="sr-only">Menu</span>
          <span aria-hidden="true">☰</span>
        </button>
        <nav id="nav-tabs" className={`nav-tabs ${open ? 'open' : ''}`} aria-label="Main">
          {TABS.map((tab) => (
            <NavLink key={tab.to} to={tab.to} end={tab.end} className="nav-tab" onClick={close}>
              {tab.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <NavLink to="/bag" className="nav-tab nav-bag" onClick={close}>
                Bag{bagCount > 0 && <span className="bag-count">{bagCount}</span>}
              </NavLink>
              <span className="nav-greeting">Hi, {user.first_name}</span>
              <button className="nav-tab nav-cta" onClick={onLogout}>
                Log out
              </button>
            </>
          ) : (
            <span className={`nav-auth ${loading ? 'pending' : ''}`}>
              <NavLink to="/login" className="nav-tab" onClick={close}>
                Log in
              </NavLink>
              <NavLink to="/create-account" className="nav-tab nav-cta" onClick={close}>
                Create account
              </NavLink>
            </span>
          )}
        </nav>
      </div>
    </header>
  )
}
