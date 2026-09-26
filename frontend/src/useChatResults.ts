import { createContext, useContext } from 'react'
import type { MatchedProduct } from './api'

export interface ChatResults {
  title: string
  query: string
  products: MatchedProduct[]
  updatedAt: number
}

export interface ChatResultsState {
  results: ChatResults | null
  showResults: (results: Omit<ChatResults, 'updatedAt'>) => void
  clearResults: () => void
}

export const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
