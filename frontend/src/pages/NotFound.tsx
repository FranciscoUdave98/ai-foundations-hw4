import { Link } from 'react-router-dom'
import { HandsomeDan, PawTrail } from '../components/Brand'

export default function NotFound() {
  return (
    <div className="container not-found">
      <HandsomeDan size={140} collar className="dan-tilt" />
      <h1>Ruff! Page not found.</h1>
      <p>Handsome Dan chased this page off campus. Let's get you back to the good stuff.</p>
      <PawTrail count={6} />
      <Link to="/" className="btn btn-primary">
        Back home
      </Link>
    </div>
  )
}
