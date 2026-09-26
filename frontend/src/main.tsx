import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource/graduate'
import '@fontsource-variable/fraunces/full.css' // includes the SOFT and WONK axes for playful headings
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './auth.tsx'
import { ChatResultsProvider } from './ChatResultsProvider.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ChatResultsProvider>
          <App />
        </ChatResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)

// Fade out the Handsome Dan splash (in index.html) once the first screen has painted.
requestAnimationFrame(() =>
  setTimeout(() => {
    const splash = document.getElementById('splash')
    if (!splash) return
    splash.classList.add('done')
    splash.addEventListener('transitionend', () => splash.remove(), { once: true })
  }, 500),
)
