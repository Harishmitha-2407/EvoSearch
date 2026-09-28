import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Documents } from '../api/client'
import { PageHeader, StatusBadge } from '../components/Layout'

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const docQuery = useQuery({
    queryKey: ['document', id],
    queryFn: () => Documents.get(id!),
    enabled: !!id,
  })

  const claimsQuery = useQuery({
    queryKey: ['document-claims', id],
    queryFn: () => Documents.claims(id!),
    enabled: !!id && docQuery.data?.status === 'ready',
  })

  const suggestionsQuery = useQuery({
    queryKey: ['document-suggestions', id],
    queryFn: () => Documents.suggestions(id!),
    enabled: !!id && docQuery.data?.status === 'ready',
  })

  const doc = docQuery.data
  if (!doc) return <div className="p-6 text-slate-500">Loading…</div>

  return (
    <div>
      <PageHeader title={doc.filename} subtitle={`Group: ${doc.group}`} />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-2 border-blue-200 dark:border-blue-700">
          <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2 uppercase tracking-wide">📊 Status</div>
          <div className="text-lg font-bold mb-3"><StatusBadge status={doc.status} /></div>
          {doc.status === 'failed' && doc.error_message && (
            <div className="text-xs text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-3 rounded-lg border border-red-300 dark:border-red-700">{doc.error_message}</div>
          )}
        </div>
        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-2 border-purple-200 dark:border-purple-700">
          <div className="text-xs font-semibold text-purple-600 dark:text-purple-400 mb-2 uppercase tracking-wide">📌 Version</div>
          <div className="text-2xl font-bold text-purple-700 dark:text-purple-300">{doc.version_label || '—'}</div>
          {doc.year && <div className="text-xs text-purple-600 dark:text-purple-400 mt-2">📅 Year: {doc.year}</div>}
        </div>
        <div className="card bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-2 border-emerald-200 dark:border-emerald-700">
          <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-2 uppercase tracking-wide">📄 File Info</div>
          <div className="text-xs text-emerald-900 dark:text-emerald-300 space-y-1">
            <div className="font-medium">{doc.file_type.toUpperCase()} • {(doc.size_bytes / 1024).toFixed(1)} KB</div>
            <div className="text-emerald-700 dark:text-emerald-400">📅 {new Date(doc.created_at).toLocaleDateString()}</div>
          </div>
        </div>
      </div>

      {doc.status === 'ready' && (
        <>
          {doc.detailed_summary && (
            <div className="card mb-8 border-2 border-blue-200 dark:border-blue-700">
              <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-4">📝 Summary</h2>
              <p className="text-base text-slate-700 dark:text-slate-300 leading-relaxed">{doc.detailed_summary}</p>
              {doc.key_topics.length > 0 && (
                <div className="mt-5 flex flex-wrap gap-2">
                  {doc.key_topics.map(topic => (
                    <span key={topic} className="badge bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border border-blue-300 dark:border-blue-600 px-3 py-1 font-medium">🏷️ {topic}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {claimsQuery.data && claimsQuery.data.length > 0 && (
            <div className="card mb-8 border-2 border-amber-200 dark:border-amber-700">
              <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-4">💬 Claims ({claimsQuery.data.length})</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {claimsQuery.data.map(claim => (
                  <div key={claim.id} className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border-2 border-amber-200 dark:border-amber-700 text-sm hover:shadow-md transition">
                    <div className="font-bold text-amber-900 dark:text-amber-200">{claim.topic}</div>
                    <div className="text-xs text-amber-800 dark:text-amber-400 mt-2 italic">{claim.normalized_statement}</div>
                    <div className="flex gap-3 mt-2 text-xs text-amber-700 dark:text-amber-400 flex-wrap">
                      {claim.requirement_strength && <span className="bg-amber-200 dark:bg-amber-800/50 px-2 py-1 rounded">💪 {claim.requirement_strength}</span>}
                      {claim.scope && <span className="bg-amber-200 dark:bg-amber-800/50 px-2 py-1 rounded">📍 {claim.scope}</span>}
                      <span className="bg-amber-200 dark:bg-amber-800/50 px-2 py-1 rounded">⭐ {(claim.importance * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {suggestionsQuery.data && suggestionsQuery.data.length > 0 && (
            <div className="card mb-8 border-2 border-emerald-200 dark:border-emerald-700">
              <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-4">💡 Suggestions ({suggestionsQuery.data.length})</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {suggestionsQuery.data.map((sugg, i) => (
                  <div key={i} className="p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border-2 border-emerald-200 dark:border-emerald-700 text-sm hover:shadow-md transition">
                    <div className="font-bold text-emerald-900 dark:text-emerald-200">🎯 {sugg.category}</div>
                    <div className="text-xs text-emerald-800 dark:text-emerald-400 mt-2">{sugg.description}</div>
                    {sugg.evidence && <div className="text-xs text-emerald-700 dark:text-emerald-400 mt-2 italic border-l-4 border-emerald-400 pl-3">📌 {sugg.evidence}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <button onClick={() => navigate('/documents')} className="mt-8 inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold transition">
        ← Back to documents
      </button>
    </div>
  )
}
