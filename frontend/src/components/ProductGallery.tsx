import { useCallback, useEffect, useRef, useState, type MouseEvent, type PointerEvent, type WheelEvent } from 'react'
import { createPortal } from 'react-dom'
import type { ProductImage } from '../api'

const ZOOM_STEPS = [1, 1.75, 2.5, 3.5]
const HOVER_ZOOM = 2.2

/** Full-screen viewer: zoom with buttons, the mouse wheel, or a double-click; drag to pan. */
function Lightbox({ images, start, onClose }: { images: ProductImage[]; start: number; onClose: () => void }) {
  const [index, setIndex] = useState(start)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const drag = useRef<{ x: number; y: number; panX: number; panY: number } | null>(null)
  const image = images[index]

  const setZoomLevel = useCallback((z: number) => {
    const next = Math.min(ZOOM_STEPS.at(-1)!, Math.max(1, z))
    setZoom(next)
    if (next === 1) setPan({ x: 0, y: 0 })
  }, [])
  const step = useCallback(
    (dir: 1 | -1) => {
      const i = ZOOM_STEPS.findIndex((z) => z >= zoom - 0.01)
      setZoomLevel(ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, i + dir))])
    },
    [zoom, setZoomLevel],
  )
  const show = useCallback(
    (i: number) => {
      setIndex((i + images.length) % images.length)
      setZoomLevel(1)
    },
    [images.length, setZoomLevel],
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === '+' || e.key === '=') step(1)
      else if (e.key === '-') step(-1)
      else if (e.key === 'ArrowRight' && images.length > 1) show(index + 1)
      else if (e.key === 'ArrowLeft' && images.length > 1) show(index - 1)
    }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [onClose, step, show, index, images.length])

  function onWheel(e: WheelEvent) {
    setZoomLevel(zoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15))
  }
  function onPointerDown(e: PointerEvent<HTMLDivElement>) {
    if (zoom === 1) return
    e.currentTarget.setPointerCapture(e.pointerId)
    drag.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y }
  }
  function onPointerMove(e: PointerEvent) {
    if (!drag.current) return
    setPan({ x: drag.current.panX + (e.clientX - drag.current.x) / zoom, y: drag.current.panY + (e.clientY - drag.current.y) / zoom })
  }

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label={`${image.alt}, zoomed`} onClick={onClose}>
      <div className="lightbox-toolbar" onClick={(e) => e.stopPropagation()}>
        <button onClick={() => step(-1)} disabled={zoom <= 1} aria-label="Zoom out">−</button>
        <span className="lightbox-zoom">{Math.round(zoom * 100)}%</span>
        <button onClick={() => step(1)} disabled={zoom >= ZOOM_STEPS.at(-1)!} aria-label="Zoom in">+</button>
        <button onClick={() => setZoomLevel(1)} disabled={zoom === 1}>Reset</button>
        <button onClick={onClose} aria-label="Close zoom">✕</button>
      </div>
      <div
        className={`lightbox-stage ${zoom > 1 ? 'zoomed' : ''}`}
        onClick={(e) => e.stopPropagation()}
        onWheel={onWheel}
        onDoubleClick={() => setZoomLevel(zoom > 1 ? 1 : 2.5)}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={() => (drag.current = null)}
      >
        <img
          src={image.url}
          alt={image.alt}
          draggable={false}
          style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)` }}
        />
      </div>
      {images.length > 1 && (
        <div className="lightbox-nav" onClick={(e) => e.stopPropagation()}>
          {images.map((img, i) => (
            <button key={img.url} className={i === index ? 'active' : ''} onClick={() => show(i)}>
              {img.kind === 'on_model' ? 'On model' : 'Product'}
            </button>
          ))}
        </div>
      )}
      <p className="lightbox-hint">Scroll or double-click to zoom · drag to move · Esc to close</p>
    </div>
  )
}

/** Product page photos: hover to magnify, click for the full-screen zoom viewer. */
export default function ProductGallery({ images }: { images: ProductImage[] }) {
  const [active, setActive] = useState(0)
  const [lens, setLens] = useState<{ x: number; y: number } | null>(null)
  const [open, setOpen] = useState(false)
  const image = images[Math.min(active, images.length - 1)]
  if (!image) return null

  function onMove(e: MouseEvent<HTMLButtonElement>) {
    const r = e.currentTarget.getBoundingClientRect()
    if (!r.width || !r.height) return
    const clamp = (v: number) => Math.min(100, Math.max(0, v))
    setLens({ x: clamp(((e.clientX - r.left) / r.width) * 100), y: clamp(((e.clientY - r.top) / r.height) * 100) })
  }

  return (
    <div className="gallery">
      <button
        type="button"
        className="detail-image zoomable"
        onMouseMove={onMove}
        onMouseLeave={() => setLens(null)}
        onClick={() => setOpen(true)}
        aria-label={`Zoom in on ${image.alt}`}
      >
        <img
          src={image.url}
          alt={image.alt}
          style={lens ? { transform: `scale(${HOVER_ZOOM})`, transformOrigin: `${lens.x}% ${lens.y}%` } : undefined}
        />
        <span className="zoom-hint" aria-hidden="true">
          🔍 Click to zoom
        </span>
      </button>
      {images.length > 1 && (
        <div className="gallery-thumbs" role="tablist" aria-label="Product photos">
          {images.map((img, i) => (
            <button
              key={img.url}
              role="tab"
              aria-selected={i === active}
              className={`gallery-thumb ${i === active ? 'active' : ''}`}
              onClick={() => setActive(i)}
            >
              <img src={img.url} alt="" />
              <span>{img.kind === 'on_model' ? 'On model' : 'Product'}</span>
            </button>
          ))}
        </div>
      )}
      {/* Portal to <body> so the viewer covers the whole window, above the nav and page animations. */}
      {open && createPortal(<Lightbox images={images} start={active} onClose={() => setOpen(false)} />, document.body)}
    </div>
  )
}
