import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Chat, Documents } from '../api/client'
import { PageHeader } from '../components/Layout'
import type { ChatMessage } from '../types'

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [groupFilter, setGroupFilter] = useState<string | undefined>(undefined)

  const groupsQuery = useQuery({ queryKey: ['doc-groups'], queryFn: Documents.groups })

  const sendMutation = useMutation({
    mutationFn: (question: string) => Chat.send(question, sessionId, undefined, groupFilter),
    onSuccess: (res) => {
      setSessionId(res.session_id)
      setMessages(prev => [...prev, { role: 'assistant', content: res.answer, sources: res.sources, confidence: res.confidence }])
    },
  })

  const send = () => {
    const q = input.trim()
    if (!q) return
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setInput('')
    sendMutation.mutate(q)
  }

  return (
    <div>
      <PageHeader title="AI Assistant" subtitle="Ask questions and get grounded answers with citations. Never invented." />

      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="flex-1">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Restrict to document group:</label>
          <select className="input w-full border-2 border-slate-300 dark:border-slate-600 focus:border-blue-500 font-medium" value={groupFilter || ''} onChange={e => setGroupFilter(e.target.value || undefined)}>
            <option value="">🌐 All documents</option>
            {groupsQuery.data?.map(g => <option key={g} value={g}>📁 {g}</option>)}
          </select>
        </div>
      </div>

      <div className="card mb-4 min-h-[480px] max-h-[600px] flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg">
        <div className="flex-1 space-y-3 overflow-y-auto pr-2">
          {messages.length === 0 && (
            <div className="text-center py-20 text-slate-500 dark:text-slate-400">
              <div className="text-4xl mb-3">💬</div>
              <p className="font-medium">Ask a question like:</p>
              <p className="text-sm mt-2">"What changed in the authentication policy?"</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-xl px-4 py-3 text-sm ${
                m.role === 'user' 
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md' 
                  : 'bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 border-2 border-slate-200 dark:border-slate-600'
              }`}>
                <p className="whitespace-pre-line leading-relaxed">{m.content}</p>
                {m.sources && m.sources.length > 0 && (
                  <div className={`mt-3 pt-2 border-t ${m.role === 'user' ? 'border-blue-400' : 'border-slate-200 dark:border-slate-600'} space-y-1`}>
                    <div className="text-xs font-medium opacity-80">📚 Sources:</div>
                    {m.sources.map((s, j) => (
                      <div key={j} className="text-xs opacity-80 flex items-center gap-1">
                        <span className="inline-block w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center text-xs font-bold">{j + 1}</span>
                        <span>{s.document_filename}{s.page ? `, p${s.page}` : ''}</span>
                        <span className="ml-auto">{(s.similarity * 100).toFixed(0)}% match</span>
                      </div>
                    ))}
                  </div>
                )}
                {typeof m.confidence === 'number' && (
                  <div className="text-xs opacity-60 mt-1">Confidence: {(m.confidence * 100).toFixed(0)}%</div>
                )}
              </div>
            </div>
          ))}
          {sendMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-xl px-4 py-3 text-sm border-2 border-slate-200 dark:border-slate-600">
                ⏳ Thinking…
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        <input
          className="input flex-1 border-2 border-slate-300 dark:border-slate-600 focus:border-blue-500"
          placeholder="🤔 Ask a question about your documents…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button className="btn-primary shrink-0" onClick={send} disabled={sendMutation.isPending}>
          {sendMutation.isPending ? '⏳ Sending' : '✉️ Send'}
        </button>
      </div>
    </div>
  )
}
