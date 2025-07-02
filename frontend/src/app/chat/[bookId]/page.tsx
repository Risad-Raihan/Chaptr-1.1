'use client'

import { useState, useRef, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpenIcon, PaperAirplaneIcon, SparklesIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import ChatMessage from '@/components/chat/ChatMessage'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  context?: {
    content: string
    chapter?: string
    similarity?: number
  }[]
}

interface BookMetadata {
  id: number
  title: string
  author: string
  page_count: number
  word_count: number
  processing_status: string
  is_embedded: boolean
}

export default function ChatPage() {
  const { bookId } = useParams()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showContext, setShowContext] = useState(false)
  const [bookMetadata, setBookMetadata] = useState<BookMetadata | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const fetchBookMetadata = async () => {
      try {
        const response = await fetch(`/api/books/${bookId}`)
        if (!response.ok) throw new Error('Failed to fetch book metadata')
        const data = await response.json()
        setBookMetadata(data)

        // If book is not processed, start processing
        if (data.processing_status === 'pending' && !data.is_embedded) {
          await processBook()
        }
      } catch (error) {
        console.error('Error fetching book metadata:', error)
      }
    }

    const processBook = async () => {
      try {
        setIsProcessing(true)
        // First, process the text
        await fetch(`/api/books/${bookId}/process`, { method: 'POST' })
        // Then, process for RAG
        await fetch(`/api/books/${bookId}/rag-process`, { method: 'POST' })
        // Refresh metadata
        const response = await fetch(`/api/books/${bookId}`)
        if (!response.ok) throw new Error('Failed to fetch book metadata')
        const data = await response.json()
        setBookMetadata(data)
      } catch (error) {
        console.error('Error processing book:', error)
      } finally {
        setIsProcessing(false)
      }
    }

    fetchBookMetadata()
  }, [bookId])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`/api/books/${bookId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      const data = await response.json()

      if (data.success) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
          context: data.context_chunks
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        throw new Error(data.error || 'Failed to get response')
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Sidebar */}
      <div className="hidden lg:flex lg:w-64 bg-gray-900 border-r border-gray-700">
        <div className="flex flex-col w-full p-4">
          <Link 
            href="/"
            className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors mb-8"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            <span>Back to Library</span>
          </Link>
          <div className="flex items-center space-x-2 mb-6">
            <BookOpenIcon className="h-6 w-6 text-primary-500" />
            <h2 className="text-xl font-semibold text-white">
              {bookMetadata?.title || 'Loading...'}
            </h2>
          </div>
          {isProcessing && (
            <div className="p-4 rounded-lg bg-primary-500/10 text-primary-300 mb-4">
              <p className="text-sm">Processing book... This may take a few minutes.</p>
            </div>
          )}
          <div className="space-y-4">
            <button
              onClick={() => setShowContext(!showContext)}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white transition-all w-full"
            >
              <SparklesIcon className="h-5 w-5" />
              <span>{showContext ? 'Hide Context' : 'Show Context'}</span>
            </button>
            {bookMetadata && (
              <div className="p-4 rounded-lg bg-gray-800/50 space-y-2">
                <p className="text-sm text-gray-400">
                  Author: <span className="text-gray-200">{bookMetadata.author || 'Unknown'}</span>
                </p>
                <p className="text-sm text-gray-400">
                  Pages: <span className="text-gray-200">{bookMetadata.page_count}</span>
                </p>
                <p className="text-sm text-gray-400">
                  Words: <span className="text-gray-200">{bookMetadata.word_count?.toLocaleString()}</span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AnimatePresence initial={false}>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <ChatMessage 
                  message={message} 
                  showContext={showContext}
                />
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-700 p-4">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value)
                  adjustTextareaHeight()
                }}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about the book..."
                className="w-full p-3 bg-gray-800 text-white rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none resize-none min-h-[44px] max-h-[150px]"
                rows={1}
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="flex items-center justify-center p-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
} 