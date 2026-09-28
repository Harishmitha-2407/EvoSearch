import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Documents, Code } from '../api/client'
import { PageHeader, StatusBadge } from '../components/Layout'
import { useTheme } from '../context/ThemeContext'

function StatCard({ label, value, icon, color }: { label: string; value: number | string; icon?: string; color?: string }) {
  const { theme } = useTheme()
  const colorClass = color || 'from-blue-400 to-blue-600'
  
  return (
    <div className={`card bg-gradient-to-br ${colorClass} text-white shadow-lg hover:shadow-xl transition border-0`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="text-sm opacity-90 font-medium">{label}</div>
          <div className="text-4xl font-bold mt-2">{value}</div>
        </div>
        {icon && <span className="text-3xl opacity-80">{icon}</span>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { theme } = useTheme()
  const docStats = useQuery({ queryKey: ['doc-stats'], queryFn: Documents.stats })
  const codeStats = useQuery({ queryKey: ['code-stats'], queryFn: Code.stats })
  const recentDocs = useQuery({ queryKey: ['recent-docs'], queryFn: () => Documents.list() })
  const recentCode = useQuery({ queryKey: ['recent-code'], queryFn: () => Code.list() })

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="An AI system for understanding how knowledge and software evolve across versions."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Documents" value={docStats.data?.total_documents ?? '—'} icon="📄" color="from-blue-400 to-blue-600" />
        <StatCard label="Document Groups" value={docStats.data?.total_groups ?? '—'} icon="📁" color="from-purple-400 to-purple-600" />
        <StatCard label="Extracted Claims" value={docStats.data?.total_claims ?? '—'} icon="💡" color="from-amber-400 to-amber-600" />
        <StatCard label="Detected Changes" value={docStats.data?.total_changes ?? '—'} icon="🔄" color="from-green-400 to-green-600" />
        <StatCard label="Code Files" value={codeStats.data?.total_files ?? '—'} icon="💻" color="from-indigo-400 to-indigo-600" />
        <StatCard label="Code Entities" value={codeStats.data?.total_entities ?? '—'} icon="⚙️" color="from-cyan-400 to-cyan-600" />
        <StatCard label="Code Changes" value={codeStats.data?.total_changes ?? '—'} icon="📊" color="from-pink-400 to-pink-600" />
        <StatCard label="Failed Documents" value={docStats.data?.failed_documents ?? '—'} icon="⚠️" color="from-red-400 to-red-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg">
          <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-slate-300 dark:border-slate-600">
            <h2 className="font-bold text-lg text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <span className="text-2xl">📄</span> Recent Documents
            </h2>
            <Link to="/documents" className="text-sm text-blue-600 dark:text-blue-400 hover:font-bold">View all →</Link>
          </div>
          <div className="space-y-2">
            {recentDocs.data?.slice(0, 6).map(d => (
              <Link
                key={d.id}
                to={`/documents/${d.id}`}
                className="flex items-center justify-between px-3 py-2 rounded-lg border-2 border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 hover:border-blue-300 transition"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate text-slate-800 dark:text-slate-200">{d.filename}</div>
                  <div className="text-xs text-slate-600 dark:text-slate-400">{d.group} {d.version_label ? `· ${d.version_label}` : ''} {d.year ? `· ${d.year}` : ''}</div>
                </div>
                <StatusBadge status={d.status} />
              </Link>
            ))}
            {recentDocs.data?.length === 0 && <div className="text-sm py-6 text-center text-slate-500 dark:text-slate-400">📁 No documents uploaded yet.</div>}
          </div>
        </div>

        <div className="card bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg">
          <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-slate-300 dark:border-slate-600">
            <h2 className="font-bold text-lg text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <span className="text-2xl">💻</span> Recent Code Files
            </h2>
            <Link to="/code" className="text-sm text-blue-600 dark:text-blue-400 hover:font-bold">View all →</Link>
          </div>
          <div className="space-y-2">
            {recentCode.data?.slice(0, 6).map(f => (
              <div
                key={f.id}
                className="flex items-center justify-between px-3 py-2 rounded-lg border-2 border-slate-200 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-700 hover:border-blue-300 transition"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate text-slate-800 dark:text-slate-200">{f.filename}</div>
                  <div className="text-xs text-slate-600 dark:text-slate-400">{f.group} · {f.language} {f.version_label ? `· ${f.version_label}` : ''}</div>
                </div>
                <StatusBadge status={f.status} />
              </div>
            ))}
            {recentCode.data?.length === 0 && <div className="text-sm py-6 text-center text-slate-500 dark:text-slate-400">📁 No code files uploaded yet.</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
