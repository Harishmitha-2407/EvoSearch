import { useQuery } from '@tanstack/react-query'
import { Health } from '../api/client'
import { PageHeader } from '../components/Layout'

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between py-4 px-4 border-b border-slate-200 dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>
      <span className={`text-sm font-bold px-3 py-1 rounded-lg ${ok === false ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'}`}>{value}</span>
    </div>
  )
}

export default function SettingsPage() {
  const healthQuery = useQuery({ queryKey: ['health'], queryFn: Health.get, refetchInterval: 15000 })
  const h = healthQuery.data

  return (
    <div>
      <PageHeader title="⚙️ Settings" subtitle="System configuration and health status" />

      <div className="card mb-8 border-2 border-blue-200 dark:border-blue-700 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
        <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-4 flex items-center gap-2">🏥 System Health</h2>
        {h ? (
          <div className="divide-y divide-blue-200 dark:divide-blue-700">
            <Row label="Overall Status" value={h.status} ok={h.status === 'ok'} />
            <Row label="Database" value={h.database} ok={h.database === 'ok'} />
            <Row label="Vector Store" value={h.vector_store} ok={!h.vector_store.includes('error')} />
            <Row label="LLM Provider" value={h.llm_provider} />
            <Row label="Embedding Model" value={h.embedding_model} />
          </div>
        ) : (
          <div className="text-sm text-blue-600 dark:text-blue-400 font-medium animate-pulse">⏳ Checking…</div>
        )}
      </div>

      <div className="card border-2 border-purple-200 dark:border-purple-700 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
        <h2 className="font-bold text-lg text-slate-900 dark:text-white mb-4 flex items-center gap-2">ℹ️ About EVOSearch</h2>
        <div className="space-y-4 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          <p>
            EVOSearch runs claim extraction, summaries, and change explanations through an LLM when 
            <code className="bg-purple-200 dark:bg-purple-900/50 px-2 py-1 rounded text-purple-900 dark:text-purple-200 font-mono font-semibold mx-1">GROQ_API_KEY</code> 
            is configured on the backend. 
          </p>
          <p>
            Without it, EVOSearch automatically falls back to deterministic heuristics — semantic search, chunking, embeddings, and code parsing always run locally regardless of LLM availability.
          </p>
          <div className="bg-white dark:bg-slate-800/50 border-2 border-purple-300 dark:border-purple-600 rounded-lg p-4 mt-4">
            <p className="text-xs font-semibold text-purple-700 dark:text-purple-300 mb-2">✨ Features:</p>
            <ul className="text-xs space-y-1 text-purple-600 dark:text-purple-400">
              <li>📊 Local semantic search & embeddings</li>
              <li>📄 Intelligent document chunking</li>
              <li>⚙️ Code analysis and parsing</li>
              <li>🤖 LLM-powered summaries (when configured)</li>
              <li>🔐 End-to-end encrypted data handling</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
