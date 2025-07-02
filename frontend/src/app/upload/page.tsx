'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<string>('')
  const router = useRouter()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setUploadStatus('Uploading file...')
    const formData = new FormData()
    formData.append('file', file)

    try {
      // Upload file
      console.log('Starting file upload...')
      const uploadResponse = await fetch('/api/books/upload', {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json()
        console.error('Upload failed:', errorData)
        throw new Error(errorData.error || 'Upload failed')
      }

      const uploadData = await uploadResponse.json()
      console.log('Upload successful:', uploadData)
      setUploadStatus('Processing book...')

      // Trigger processing
      console.log('Starting book processing...')
      const processResponse = await fetch(`/api/books/${uploadData.book_id}/process`, {
        method: 'POST',
      })

      if (!processResponse.ok) {
        const errorData = await processResponse.json()
        console.error('Processing failed:', errorData)
        throw new Error(errorData.error || 'Processing failed')
      }

      const processData = await processResponse.json()
      console.log('Processing successful:', processData)
      setUploadStatus('Success! Redirecting...')
      
      router.push(`/chat/${uploadData.book_id}`)
    } catch (error) {
      console.error('Error details:', error)
      alert('Failed to upload or process file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Upload Your Book</h2>
            <p className="mt-2 text-sm text-gray-600">
              Upload a PDF or ePub file to start chatting with your book
            </p>
          </div>

          <div className="mt-8 space-y-6">
            <div>
              <label 
                htmlFor="file-upload" 
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Choose a file
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div className="space-y-1 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    stroke="currentColor"
                    fill="none"
                    viewBox="0 0 48 48"
                    aria-hidden="true"
                  >
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="file-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                    >
                      <span>Upload a file</span>
                      <input
                        id="file-upload"
                        name="file-upload"
                        type="file"
                        className="sr-only"
                        accept=".pdf,.epub"
                        onChange={handleFileChange}
                      />
                    </label>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-gray-500">PDF or ePub up to 10MB</p>
                </div>
              </div>
              {file && (
                <p className="mt-2 text-sm text-gray-500">
                  Selected file: {file.name}
                </p>
              )}
            </div>

            {uploadStatus && (
              <div className="text-sm text-gray-600 text-center">
                {uploadStatus}
              </div>
            )}

            <div>
              <button
                onClick={handleUpload}
                disabled={!file || isUploading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isUploading ? 'Processing...' : 'Upload Book'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 