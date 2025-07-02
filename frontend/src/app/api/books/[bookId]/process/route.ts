import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  req: NextRequest,
  { params }: { params: { bookId: string } }
) {
  try {
    const response = await fetch(
      `${process.env.NEXT_API_URL}/books/${params.bookId}/process`,
      {
        method: 'POST',
      }
    )

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Processing failed' }))
      console.error('Processing failed:', errorData)
      throw new Error(errorData.detail || 'Processing failed')
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error processing book:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to process book' },
      { status: 500 }
    )
  }
} 