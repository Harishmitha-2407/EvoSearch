import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search } from '../api/client'
import { PageHeader } from '../components/Layout'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const searchMutation = useMutation({ mutationFn: (q: string) => Search.query(q, 10) })

  const runSearch = () => {
    if (query.trim()) searchMutation.mutate(query.trim())
  }

  return (
    <div>
      <PageHeader title="Semantic Search" subtitle="Search across every uploaded document by meaning, not just keywords." />

      <div className="mb-6 flex gap-3">
        <input
          className="input flex-1 border-2 border-slate-300 dark:border-slate-600 focus:border-blue-500 font-medium"
          placeholder="🔍 e.g. What are the password requirements?"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && runSearch()}
        />
        <button className="btn-primary shrink-0" onClick={runSearch} disabled={searchMutation.isPending}>
          {searchMutation.isPending ? '⏳ Searching…' : '🔍 Search'}
        </button>
      </div>

      {searchMutation.data?.insufficient_evidence && (
        <div className="text-sm text-amber-800 dark:text-amber-200 bg-amber-50 dark:bg-amber-900 rounded-lg px-4 py-4 mb-6 border-2 border-amber-200 dark:border-amber-700">
          ⚠️ No results met the similarity threshold — try rephrasing your query or this topic may not be covered in your documents.
        </div>
      )}

      <div className="space-y-4">
        {searchMutation.data?.results.length === 0 && !searchMutation.data?.insufficient_evidence && (
          <div className="text-center py-12 text-slate-500 dark:text-slate-400">
            💭 Start typing to search across all your documents
          </div>
        )}
        {searchMutation.data?.results.map((r, idx) => (
          <div key={r.chunk_id} className="card bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 hover:shadow-lg transition">
            <div className="flex items-start justify-between mb-3 pb-3 border-b-2 border-slate-200 dark:border-slate-700">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="inline-block w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-xs">
                    {idx + 1}
                  </span>
                  <Link to={`/documents/${r.document_id}`} className="font-bold text-blue-600 dark:text-blue-400 hover:underline">
                    {r.document_filename}
                  </Link>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                  {r.group && <span className="bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">📁 {r.group}</span>}
                  {r.year && <span className="bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">📅 {r.year}</span>}
                  {r.page && <span className="bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">📄 page {r.page}</span>}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-green-600 dark:text-green-400">{(r.similarity * 100).toFixed(1)}%</div>
                <div className="text-xs text-slate-600 dark:text-slate-400">match</div>
              </div>
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-blue-50 dark:bg-slate-800 p-3 rounded-lg border-l-4 border-blue-400">
              {r.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
