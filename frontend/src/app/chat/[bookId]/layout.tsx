'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { BookOpenIcon, ChevronLeftIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'

interface BookMetadata {
  id: number
  title: string
  author: string
  page_count: number
  word_count: number
  processing_status: string
}

export default function ChatLayout({
  children,
  params
}: {
  children: React.ReactNode
  params: { bookId: string }
}) {
  const router = useRouter()
  const [bookMetadata, setBookMetadata] = useState<BookMetadata | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchBookMetadata = async () => {
      try {
        const response = await fetch(`/api/books/${params.bookId}`)
        if (!response.ok) throw new Error('Failed to fetch book metadata')
        const data = await response.json()
        setBookMetadata(data)
      } catch (error) {
        console.error('Error fetching book metadata:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBookMetadata()
  }, [params.bookId])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
          <p className="text-gray-400">Loading book details...</p>
        </div>
      </div>
    )
  }

  if (!bookMetadata) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold text-white">Book Not Found</h2>
          <p className="text-gray-400">The book you're looking for doesn't exist or you don't have access to it.</p>
          <Link 
            href="/"
            className="inline-flex items-center space-x-2 text-primary-500 hover:text-primary-400 transition-colors"
          >
            <ChevronLeftIcon className="h-5 w-5" />
            <span>Return to Library</span>
          </Link>
        </div>
      </div>
    )
  }

  return children
} 