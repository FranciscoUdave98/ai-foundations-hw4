// Campus Customs brand art: original SVG illustrations inspired by Yale's bulldog mascot
// (Handsome Dan) and Yale colors. These are not Yale's official trademarked logos; a licensed
// retailer would swap in the official artwork provided under its Yale license.

interface ArtProps {
  size?: number
  className?: string
  title?: string
}

const NAVY = '#00356b'

/** Handsome Dan, the Yale bulldog: white face, navy brindle patch, and the famous underbite. */
export function HandsomeDan({ size = 64, className, title, collar = false }: ArtProps & { collar?: boolean }) {
  return (
    <svg
      width={size}
      height={collar ? size * 1.1 : size}
      viewBox={collar ? '0 0 120 132' : '0 0 120 120'}
      className={`dan ${className ?? ''}`}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <g stroke={NAVY} strokeWidth="3.2" strokeLinejoin="round" strokeLinecap="round">
        <path className="dan-ear dan-ear-left" d="M26 36 C12 26 3 42 9 56 C15 52 22 46 31 41 Z" fill={NAVY} />
        <path className="dan-ear dan-ear-right" d="M94 36 C108 26 117 42 111 56 C105 52 98 46 89 41 Z" fill={NAVY} />
        <path d="M60 20 C84 20 100 30 102 50 C104 62 108 78 100 92 C94 102 78 108 60 108 C42 108 26 102 20 92 C12 78 16 62 18 50 C20 30 36 20 60 20 Z" fill="#fff" />
        <path d="M70 38 C80 34 91 40 91 50 C91 58 83 60 77 58 C71 56 66 48 70 38 Z" fill={NAVY} stroke="none" />
        <path d="M44 33 Q51 29 58 33" fill="none" strokeWidth="2.4" />
        <path d="M62 33 Q69 29 76 33" fill="none" strokeWidth="2.4" />
        <path d="M52 39 Q60 36 68 39" fill="none" strokeWidth="2.4" />
        <g className="dan-eyes">
          <circle cx="43" cy="50" r="5.5" fill={NAVY} stroke="none" />
          <circle cx="44.8" cy="48.2" r="1.6" fill="#fff" stroke="none" />
          <circle cx="79" cy="49" r="5.2" fill="#fff" stroke="none" />
          <circle cx="79" cy="49" r="3.5" fill={NAVY} stroke="none" />
          <circle cx="80.3" cy="47.7" r="1.2" fill="#fff" stroke="none" />
        </g>
        <path d="M37 82 C39 99 81 99 83 82 C74 88 46 88 37 82 Z" fill="#fff" />
        <path d="M60 71 V76" fill="none" strokeWidth="2.6" />
        <path d="M60 76 C55 85 38 85 30 75" fill="#fff" strokeWidth="2.8" />
        <path d="M60 76 C65 85 82 85 90 75" fill="#fff" strokeWidth="2.8" />
        <path d="M42 88 L45.5 74 L49.5 86 Z" fill="#fff" strokeWidth="2.2" />
        <path d="M70.5 86 L74.5 74 L78 88 Z" fill="#fff" strokeWidth="2.2" />
        <g className="dan-nose">
          <path d="M47 62 C47 55 73 55 73 62 C73 68 66 71 60 71 C54 71 47 68 47 62 Z" fill={NAVY} />
          <ellipse cx="54" cy="61" rx="2.4" ry="1.4" fill="#fff" stroke="none" />
        </g>
      </g>
      {collar && (
        <g>
          <path d="M28 100 Q60 116 92 100 L94 110 Q60 128 26 110 Z" fill={NAVY} />
          <circle cx="60" cy="118" r="9" fill="#fff" stroke={NAVY} strokeWidth="3" />
          <text x="60" y="122.5" textAnchor="middle" fontFamily="Graduate, Georgia, serif" fontSize="12" fill={NAVY}>
            Y
          </text>
        </g>
      )}
    </svg>
  )
}

/** A navy shield with a varsity "Y" and 1701, Yale's founding year. */
export function YaleShield({ size = 48, className, title, color = NAVY }: ArtProps & { color?: string }) {
  const ink = color === NAVY ? '#fff' : NAVY
  return (
    <svg
      width={size}
      height={size * 1.18}
      viewBox="0 0 100 118"
      className={className}
      role={title ? 'img' : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <path d="M8 6 H92 V52 C92 82 72 100 50 112 C28 100 8 82 8 52 Z" fill={color} />
      <path d="M15 13 H85 V52 C85 77 68 92 50 103 C32 92 15 77 15 52 Z" fill="none" stroke={ink} strokeWidth="2.5" />
      <text x="50" y="68" textAnchor="middle" fontFamily="Graduate, Georgia, serif" fontSize="46" fill={ink}>
        Y
      </text>
      <text x="50" y="86" textAnchor="middle" fontFamily="Georgia, serif" fontSize="9" letterSpacing="2" fill={ink}>
        1701
      </text>
    </svg>
  )
}

/** "YALE UNIVERSITY" set in varsity type. */
export function YaleWordmark({ width = 220, className, color = NAVY }: { width?: number; className?: string; color?: string }) {
  return (
    <svg width={width} height={width * 0.22} viewBox="0 0 360 80" className={className} role="img" aria-label="Yale University">
      <text x="180" y="48" textAnchor="middle" fontFamily="Graduate, Georgia, serif" fontSize="46" letterSpacing="10" fill={color}>
        YALE
      </text>
      <text x="180" y="72" textAnchor="middle" fontFamily="Georgia, serif" fontSize="13" letterSpacing="6" fill={color}>
        UNIVERSITY
      </text>
    </svg>
  )
}

/** A single bulldog paw print. */
export function Paw({ size = 20, className, color = NAVY }: { size?: number; className?: string; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" className={className} aria-hidden="true" fill={color}>
      <ellipse cx="20" cy="27" rx="9" ry="7.5" />
      <ellipse cx="9" cy="17" rx="3.6" ry="4.6" transform="rotate(-20 9 17)" />
      <ellipse cx="16" cy="10.5" rx="3.6" ry="4.8" />
      <ellipse cx="24" cy="10.5" rx="3.6" ry="4.8" />
      <ellipse cx="31" cy="17" rx="3.6" ry="4.6" transform="rotate(20 31 17)" />
    </svg>
  )
}

/** A trail of paw prints that "walk" in one after another (used in loaders and dividers). */
export function PawTrail({ count = 5, className, color }: { count?: number; className?: string; color?: string }) {
  return (
    <span className={`paw-trail ${className ?? ''}`} aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <span key={i} style={{ animationDelay: `${i * 0.18}s` }} className={i % 2 ? 'paw-up' : 'paw-down'}>
          <Paw size={16} color={color} />
        </span>
      ))}
    </span>
  )
}

/** Friendly loading state: Handsome Dan bobbing along with a walking paw trail. */
export function BulldogLoader({ label = 'Fetching the goods…' }: { label?: string }) {
  return (
    <div className="bulldog-loader" role="status" aria-live="polite">
      <HandsomeDan size={72} className="dan-bounce" />
      <PawTrail />
      <p>{label}</p>
    </div>
  )
}
