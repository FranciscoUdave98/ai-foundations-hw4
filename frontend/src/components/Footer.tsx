import { Link } from 'react-router-dom'
import { HandsomeDan, PawTrail, YaleShield, YaleWordmark } from './Brand'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <YaleShield size={44} color="#ffffff" />
          <div>
            <strong>Campus Customs</strong>
            <p>57 Broadway, New Haven, CT · Open seven days a week</p>
          </div>
        </div>
        <nav aria-label="Footer">
          <Link to="/products">Shop</Link>
          <Link to="/about">Our story</Link>
          <Link to="/create-account">Create account</Link>
        </nav>
      </div>
      <div className="footer-cheer">
        <HandsomeDan size={46} className="dan-wiggle" />
        <YaleWordmark width={170} color="#ffffff" />
        <span className="footer-cheer-text">Go Bulldogs!</span>
        <PawTrail count={4} color="#ffffff" />
      </div>
      <p className="footer-note">Family-owned and dressing Bulldogs since 1975.</p>
    </footer>
  )
}
