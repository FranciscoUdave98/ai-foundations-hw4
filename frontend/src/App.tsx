import { Route, Routes, useLocation } from 'react-router-dom'
import { PawTrail } from './components/Brand'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import NavBar from './components/NavBar'
import About from './pages/About'
import Bag from './pages/Bag'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import ProductPage from './pages/ProductPage'
import Products from './pages/Products'
import { useAuth } from './useAuth'

export default function App() {
  const { user, loading } = useAuth()
  const location = useLocation()
  return (
    <div className="app">
      <NavBar />
      {/* Keyed by path: every page change replays the paw-print progress bar and the page entrance. */}
      <div key={`progress-${location.pathname}`} className="route-progress" aria-hidden="true">
        <span className="route-progress-bar" />
        <PawTrail count={4} className="route-progress-paws" />
      </div>
      <main key={location.pathname} className="page page-enter">
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/bag" element={<Bag />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      {/* Remount per user so a new login loads that shopper's saved chat. */}
      {!loading && <ChatWidget key={user?.id ?? 'guest'} />}
    </div>
  )
}
