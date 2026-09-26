import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CATEGORIES, getProducts, type ProductSummary } from '../api'
import { HandsomeDan, Paw, PawTrail, YaleShield, YaleWordmark } from '../components/Brand'
import ProductCard from '../components/ProductCard'
import { openChat } from '../openChat'

const FEATURED = [
  'district-vit-hoodie-vintage-bulldog',
  'champion-reverse-weave-crewneck',
  'boola-boola-t-shirt',
  'benjamin-franklin-1-4-zip',
]
const HERO = ['basic-hoodie-big-yale', 'super-heavyweight-crewneck-arched-yale-crest', 'yale-bowl-t-shirt']

const CHEERS = ['Go Bulldogs', 'Boola Boola', 'Since 1975', '57 Broadway', 'Printed in New Haven', 'For God, for Country, and for Yale']

const PROMISES = [
  {
    icon: 'shield',
    title: 'Tradition you can wear',
    text: "We opened across from campus in 1975 and have been New Haven's go-to for official Yale gear ever since. Every piece carries a little of that history.",
  },
  {
    icon: 'paw',
    title: 'Printed down the street',
    text: 'Our screen printing and embroidery happen in our own Broadway shop, so designs come out crisp and new drops land fast.',
  },
  {
    icon: 'dan',
    title: 'A family shop that knows you',
    text: "We're still family-run and open seven days a week. Come in with a question and leave with the right fit — no rush, no hard sell.",
  },
]

export default function Home() {
  const [products, setProducts] = useState<ProductSummary[]>([])

  useEffect(() => {
    getProducts().then(setProducts).catch(() => setProducts([]))
  }, [])

  const byId = new Map(products.map((p) => [p.product_id, p]))
  const featured = FEATURED.map((id) => byId.get(id)).filter((p): p is ProductSummary => !!p)
  const hero = HERO.map((id) => byId.get(id)).filter((p): p is ProductSummary => !!p)

  return (
    <>
      <section className="hero">
        <YaleShield size={420} className="hero-watermark" color="#ffffff" />
        <div className="hero-copy">
          <span className="eyebrow eyebrow-light">Since 1975 · 57 Broadway, New Haven</span>
          <h1>
            <span className="hero-kicker">Yale spirit,</span> made right across the street.
          </h1>
          <p>
            Crewnecks, hoodies, and tees for every residential college, team, and tradition — designed, printed, and
            stitched in New Haven by the family that has been outfitting Bulldogs for fifty years.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-light">
              Shop the collection
            </Link>
            <button type="button" className="btn btn-ghost" onClick={() => openChat()}>
              <HandsomeDan size={26} /> Ask the Bulldog
            </button>
          </div>
        </div>
        <div className="hero-collage" aria-hidden={hero.length === 0}>
          {hero.map((p, i) => (
            <Link key={p.product_id} to={`/products/${p.product_id}`} className={`hero-tile hero-tile-${i}`}>
              <img src={p.image_url} alt={p.name} />
            </Link>
          ))}
          <HandsomeDan size={120} collar className="hero-dan dan-bounce" title="Handsome Dan, the Yale bulldog" />
        </div>
      </section>

      <div className="cheer-ribbon" aria-hidden="true">
        <div className="cheer-track">
          {[...CHEERS, ...CHEERS].map((c, i) => (
            <span key={i}>
              {c} <Paw size={16} color="#ffffff" />
            </span>
          ))}
        </div>
      </div>

      <section className="section">
        <div className="section-head">
          <h2>Why students shop with us</h2>
          <p>Old-school Yale pride with the pace of a modern campus.</p>
        </div>
        <div className="promise-grid">
          {PROMISES.map((p) => (
            <article key={p.title} className="promise">
              <span className="promise-icon">
                {p.icon === 'shield' ? <YaleShield size={34} /> : p.icon === 'paw' ? <Paw size={34} /> : <HandsomeDan size={40} />}
              </span>
              <h3>{p.title}</h3>
              <p>{p.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head section-head-row">
          <div>
            <h2>Fresh picks for campus</h2>
            <p>Bulldog classics that go from lecture to the Yale Bowl.</p>
          </div>
          <Link to="/products" className="link-arrow">
            See all products →
          </Link>
        </div>
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Shop by style</h2>
        </div>
        <div className="category-row">
          {CATEGORIES.map((c) => (
            <Link key={c} to={`/products?category=${encodeURIComponent(c)}`} className="category-pill">
              {c}
            </Link>
          ))}
        </div>
      </section>

      <section className="banner">
        <HandsomeDan size={88} collar className="banner-dan dan-wiggle" />
        <div>
          <YaleWordmark width={150} color="#ffffff" className="banner-wordmark" />
          <h2>Rep your residential college</h2>
          <p>From Benjamin Franklin to Timothy Dwight, find the crest that feels like home.</p>
        </div>
        <Link to="/products?q=college" className="btn btn-light">
          Find your college
        </Link>
      </section>
      <PawTrail count={9} className="section-paws" />
    </>
  )
}
