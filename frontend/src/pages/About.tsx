import { Link } from 'react-router-dom'
import { HandsomeDan, PawTrail, YaleShield, YaleWordmark } from '../components/Brand'

const MILESTONES = [
  { year: '1975', text: 'A small Yale memorabilia shop opens on Broadway, directly across from campus.' },
  { year: '1990s', text: 'We bring screen printing and embroidery in-house, right here in New Haven.' },
  { year: 'Today', text: 'Still family-run, now designing, printing, and shipping gear for students, teams, and alumni.' },
]

const SERVICES = [
  { title: 'Screen printing', text: 'Bold, durable prints for club shirts, dorm tees, and game-day gear.' },
  { title: 'Embroidery', text: 'Clean stitched crests and wordmarks for crewnecks, quarter-zips, and jackets.' },
  { title: 'Design help', text: 'Bring a rough idea; our team will help turn it into something worth wearing.' },
  { title: 'Group & event orders', text: 'Teams, a cappella groups, reunions — we handle the whole order from art to delivery.' },
]

export default function About() {
  return (
    <div className="container about">
      <section className="about-hero">
        <div className="about-mascot" aria-hidden="true">
          <HandsomeDan size={170} collar className="dan-bounce" />
          <YaleWordmark width={190} />
        </div>
        <span className="eyebrow">About Campus Customs</span>
        <h1>Fifty years of Yale pride, one Broadway storefront.</h1>
        <p>
          Campus Customs began in 1975 as a tiny shop selling Yale keepsakes across the street from Old Campus. Half a
          century later we are still family-owned, still on Broadway, and still the place students stop between classes
          for the sweatshirt they will wear for the next four years — and long after.
        </p>
      </section>

      <section className="about-grid">
        <article className="about-card">
          <YaleShield size={36} className="about-card-icon" />
          <h2>Our story</h2>
          <ol className="timeline">
            {MILESTONES.map((m) => (
              <li key={m.year}>
                <strong>{m.year}</strong>
                <span>{m.text}</span>
              </li>
            ))}
          </ol>
        </article>
        <article className="about-card">
          <HandsomeDan size={42} className="about-card-icon" />
          <h2>What we believe</h2>
          <p>
            Great merch starts with great service. We treat every customer like a regular, keep our business honest,
            and would rather be your shop for all four years than make a single quick sale.
          </p>
          <p>
            We honor tradition, but we move at campus speed: because design, printing, and shipping all happen under one
            roof, your order is ready fast without cutting corners.
          </p>
        </article>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>What we make</h2>
          <p>We do nearly everything in our own New Haven shop.</p>
        </div>
        <div className="promise-grid promise-grid-4">
          {SERVICES.map((s) => (
            <article key={s.title} className="promise">
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </article>
          ))}
        </div>
      </section>

      <PawTrail count={9} className="section-paws" />
      <section className="banner">
        <HandsomeDan size={88} collar className="banner-dan dan-wiggle" />
        <div>
          <h2>Come say hi</h2>
          <p>57 Broadway, New Haven · Open seven days a week. Planning shirts for your team or club? Stop in and we'll show you what's possible.</p>
        </div>
        <Link to="/products" className="btn btn-light">
          Browse the shop
        </Link>
      </section>
    </div>
  )
}
