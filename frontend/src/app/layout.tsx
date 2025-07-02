import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Providers } from './providers'
import { Suspense } from 'react'

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export const metadata: Metadata = {
  title: 'Chaptr',
  description: 'RAG-powered book analysis and chat tool',
  keywords: ['books', 'AI', 'analysis', 'reading', 'chat'],
  authors: [{ name: 'Chaptr Team' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Suspense fallback={<div className="min-h-screen bg-gray-50 flex items-center justify-center">Loading...</div>}>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
          </Suspense>
        </Providers>
      </body>
    </html>
  )
} 