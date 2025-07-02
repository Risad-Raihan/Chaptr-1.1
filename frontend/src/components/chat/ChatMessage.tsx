import { motion } from 'framer-motion'
import { UserCircleIcon } from '@heroicons/react/24/solid'
import { BookOpenIcon } from '@heroicons/react/24/outline'
import ReactMarkdown from 'react-markdown'
import { format } from 'date-fns'

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

interface ChatMessageProps {
  message: Message
  showContext?: boolean
}

export default function ChatMessage({
  message,
  showContext = false
}: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}
    >
      <div className={`
        flex items-start space-x-3 max-w-[80%]
        ${isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'}
      `}>
        {/* Avatar */}
        <div className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser ? 'bg-primary-600' : 'bg-gray-700'}
        `}>
          {isUser ? (
            <UserCircleIcon className="w-8 h-8 text-white" />
          ) : (
            <BookOpenIcon className="w-5 h-5 text-primary-400" />
          )}
        </div>

        {/* Message Content */}
        <div className={`
          flex flex-col
          ${isUser ? 'items-end' : 'items-start'}
        `}>
          {/* Timestamp */}
          <span className="text-xs text-gray-500 mb-1">
            {format(message.timestamp, 'HH:mm')}
          </span>

          {/* Message Bubble */}
          <div className={`
            rounded-2xl p-4 shadow-lg
            ${isUser 
              ? 'bg-primary-600 text-white' 
              : 'bg-gray-800 text-gray-100'}
            ${message.context && showContext ? 'mb-2' : ''}
          `}>
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>

          {/* Context Section */}
          {message.context && showContext && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="w-full mt-2 space-y-2"
            >
              {message.context.map((ctx, i) => (
                <div
                  key={i}
                  className={`
                    relative p-3 rounded-lg text-sm
                    bg-gray-800/50 border border-gray-700
                    hover:bg-gray-800 transition-colors
                  `}
                >
                  {ctx.chapter && (
                    <div className="flex items-center space-x-2 mb-1 text-primary-400">
                      <BookOpenIcon className="w-4 h-4" />
                      <span>Chapter {ctx.chapter}</span>
                      {ctx.similarity && (
                        <span className="text-gray-500">
                          ({Math.round(ctx.similarity * 100)}% match)
                        </span>
                      )}
                    </div>
                  )}
                  <p className="text-gray-300">{ctx.content}</p>
                </div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  )
} 