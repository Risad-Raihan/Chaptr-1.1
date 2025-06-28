import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Chaptr',
  description: 'RAG-powered book analysis and chat tool',
  keywords: ['books', 'AI', 'analysis', 'reading', 'chat'],
  authors: [{ name: 'Chaptr Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  )
} 