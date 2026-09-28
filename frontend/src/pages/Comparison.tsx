import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Documents, Comparison } from '../api/client'
import { PageHeader } from '../components/Layout'

const changeColor: Record<string, string> = {
  ADDED: 'bg-emerald-100 text-emerald-700',
  REMOVED: 'bg-red-100 text-red-700',
  MODIFIED: 'bg-amber-100 text-amber-700',
  UNCHANGED: 'bg-slate-100 text-slate-500',
}

export default function ComparisonPage() {
  const [group, setGroup] = useState<string | undefined>(undefined)
  const [docA, setDocA] = useState<string>('')
  const [docB, setDocB] = useState<string>('')

  const groupsQuery = useQuery({ queryKey: ['doc-groups'], queryFn: Documents.groups })
  const docsQuery = useQuery({
    queryKey: ['documents', group],
    queryFn: () => Documents.list(group),
    enabled: !!group,
  })

  const compareMutation = useMutation({
    mutationFn: () => Comparison.compare(docA, docB),
  })

  return (
    <div>
      <PageHeader title="Version Comparison" subtitle="Compare claims between two document versions — added, removed, modified, unchanged." />

      <div className="card bg-gradient-to-br from-blue-50 to-slate-50 dark:from-slate-800 dark:to-slate-900 border-2 border-blue-200 dark:border-slate-700 shadow-lg mb-6">
        <h2 className="font-bold text-lg text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
          <span className="text-2xl">📊</span> Compare Document Versions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">📁 Document Group</label>
            <select className="input w-full border-2" value={group || ''} onChange={e => { setGroup(e.target.value || undefined); setDocA(''); setDocB('') }}>
              <option value="">Select group…</option>
              {groupsQuery.data?.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">📄 Older Version (A)</label>
            <select className="input w-full border-2" value={docA} onChange={e => setDocA(e.target.value)} disabled={!group}>
              <option value="">Select version…</option>
              {docsQuery.data?.map(d => <option key={d.id} value={d.id}>{d.filename} {d.year ? `(${d.year})` : ''}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">📄 Newer Version (B)</label>
            <select className="input w-full border-2" value={docB} onChange={e => setDocB(e.target.value)} disabled={!group}>
              <option value="">Select version…</option>
              {docsQuery.data?.map(d => <option key={d.id} value={d.id}>{d.filename} {d.year ? `(${d.year})` : ''}</option>)}
            </select>
          </div>
        </div>
        <button
          className="btn-primary mt-4 w-full"
          disabled={!docA || !docB || docA === docB || compareMutation.isPending}
          onClick={() => compareMutation.mutate()}
        >
          {compareMutation.isPending ? '⏳ Comparing…' : '🔄 Compare Versions'}
        </button>
        {compareMutation.error && (
          <div className="text-sm text-red-700 dark:text-red-200 mt-3 bg-red-50 dark:bg-red-900 border-2 border-red-200 dark:border-red-700 rounded-lg px-3 py-2">
            ❌ Comparison failed — make sure both documents finished processing.
          </div>
        )}
      </div>

      {compareMutation.data && (
        <>
          <div className="card bg-gradient-to-r from-purple-400 to-blue-500 text-white shadow-lg mb-6 border-0">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-90 font-medium">📈 EVOSearch Evolution Score</div>
                <div className="text-5xl font-bold mt-2 flex items-baseline gap-2">
                  {compareMutation.data.evolution_score.score}
                  <span className="text-2xl opacity-75">/100</span>
                </div>
                <div className="text-xs opacity-75 mt-1">A project-defined score measuring overall change magnitude</div>
              </div>
              <div className="text-6xl opacity-30">📊</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
            {Object.entries(compareMutation.data.evolution_score.factors).map(([k, v]) => (
              <div key={k} className={`card border-2 shadow-md ${
                k === 'ADDED' ? 'bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900 dark:to-emerald-800 border-emerald-300 dark:border-emerald-700' :
                k === 'REMOVED' ? 'bg-gradient-to-br from-red-100 to-red-50 dark:from-red-900 dark:to-red-800 border-red-300 dark:border-red-700' :
                k === 'MODIFIED' ? 'bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-900 dark:to-amber-800 border-amber-300 dark:border-amber-700' :
                'bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-700 dark:to-slate-600 border-slate-300 dark:border-slate-600'
              }`}>
                <div className="text-3xl font-bold">{v}</div>
                <div className="text-xs font-medium mt-1 opacity-75">{k}</div>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            {compareMutation.data.changes.length === 0 ? (
              <div className="card text-center py-12 bg-green-50 dark:bg-green-900 border-2 border-green-200 dark:border-green-700">
                <div className="text-4xl mb-2">✓</div>
                <p className="text-lg text-green-800 dark:text-green-200 font-medium">No differences detected</p>
                <p className="text-sm text-green-700 dark:text-green-300">Both versions are identical.</p>
              </div>
            ) : (
              compareMutation.data.changes.map(ch => (
                <div key={ch.id} className="card bg-gradient-to-br from-white to-slate-50 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-md hover:shadow-lg transition">
                  <div className="flex items-center justify-between mb-3 pb-3 border-b-2 border-slate-200 dark:border-slate-700">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="badge bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold px-2 py-1 rounded">📌 {ch.topic}</span>
                      <span className={`badge font-bold px-2 py-1 rounded ${changeColor[ch.change_type] || 'bg-slate-100 text-slate-600'}`}>
                        {ch.change_type === 'ADDED' && '✨'} {ch.change_type === 'REMOVED' && '🗑️'} {ch.change_type === 'MODIFIED' && '✏️'} {ch.change_type === 'UNCHANGED' && '✓'}
                        {' '}{ch.change_type}
                      </span>
                      {ch.semantic_change && <span className="badge bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 text-xs px-2 py-1 rounded">🔄 {ch.semantic_change.replaceAll('_', ' ')}</span>}
                    </div>
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">📊 {(ch.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div className="bg-red-50 dark:bg-red-900 p-3 rounded-lg border-l-4 border-red-400">
                      <div className="text-xs font-bold text-red-800 dark:text-red-200 mb-1">← Previous</div>
                      <p className="text-sm text-red-900 dark:text-red-100">{ch.previous_text || '(not present)'}</p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900 p-3 rounded-lg border-l-4 border-green-400">
                      <div className="text-xs font-bold text-green-800 dark:text-green-200 mb-1">→ Current</div>
                      <p className="text-sm font-medium text-green-900 dark:text-green-100">{ch.current_text || '(removed)'}</p>
                    </div>
                  </div>
                  {ch.explanation && <p className="text-xs text-slate-600 dark:text-slate-400 italic bg-slate-50 dark:bg-slate-800 p-2 rounded border-l-4 border-slate-400">💡 {ch.explanation}</p>}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  )
}
