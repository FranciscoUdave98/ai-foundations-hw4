import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { ChatResultsContext, type ChatResults } from './useChatResults'

// Holds the latest product matches from the chat so any page can render them.
export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  const showResults = useCallback(
    (r: Omit<ChatResults, 'updatedAt'>) => setResults({ ...r, updatedAt: Date.now() }),
    [],
  )
  const clearResults = useCallback(() => setResults(null), [])
  const value = useMemo(() => ({ results, showResults, clearResults }), [results, showResults, clearResults])
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}
