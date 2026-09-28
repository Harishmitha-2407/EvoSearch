import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Documents } from '../api/client'
import { PageHeader, StatusBadge } from '../components/Layout'

export default function DocumentsPage() {
  const qc = useQueryClient()
  const [group, setGroup] = useState('')
  const [versionLabel, setVersionLabel] = useState('')
  const [year, setYear] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [filterGroup, setFilterGroup] = useState<string | undefined>(undefined)

  const groupsQuery = useQuery({ queryKey: ['doc-groups'], queryFn: Documents.groups })
  const listQuery = useQuery({ queryKey: ['documents', filterGroup], queryFn: () => Documents.list(filterGroup) })

  const uploadMutation = useMutation({
    mutationFn: () => Documents.upload(file as File, group || 'Ungrouped', versionLabel || undefined, year ? Number(year) : undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['doc-groups'] })
      qc.invalidateQueries({ queryKey: ['doc-stats'] })
      setFile(null)
      setGroup('')
      setVersionLabel('')
      setYear('')
    },
    onError: (error: any) => {
      console.error('Upload error:', error)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => Documents.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] })
      qc.invalidateQueries({ queryKey: ['doc-stats'] })
    },
  })

  return (
    <div>
      <PageHeader title="Documents" subtitle="Upload documents and track them across versions." />

      <div className="card bg-gradient-to-br from-blue-50 to-slate-50 dark:from-slate-800 dark:to-slate-900 border-2 border-blue-200 dark:border-slate-700 shadow-lg mb-6">
        <h2 className="font-bold text-lg text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
          <span className="text-2xl">📤</span> Upload a Document
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} className="input md:col-span-1 border-2" />
          <input placeholder="Group (e.g. Security Policy)" value={group} onChange={e => setGroup(e.target.value)} className="input border-2" />
          <input placeholder="Version label (e.g. v2025)" value={versionLabel} onChange={e => setVersionLabel(e.target.value)} className="input border-2" />
          <input placeholder="Year (e.g. 2025)" value={year} onChange={e => setYear(e.target.value)} className="input border-2" />
        </div>
        <div className="mt-4 flex items-center gap-3">
          <button
            className="btn-primary"
            disabled={!file || uploadMutation.isPending}
            onClick={() => uploadMutation.mutate()}
          >
            {uploadMutation.isPending ? '⏳ Uploading & processing…' : '✓ Upload'}
          </button>
          <span className="text-xs text-slate-600 dark:text-slate-400">Supports PDF, DOCX, TXT, Markdown, CSV, JSON, YAML</span>
        </div>
        {uploadMutation.data?.status === 'failed' && (
          <div className="mt-3 text-sm text-red-700 bg-red-50 dark:bg-red-900 dark:text-red-200 border-2 border-red-200 dark:border-red-700 rounded-lg px-3 py-2">
            ❌ Processing failed: {uploadMutation.data.error_message}
          </div>
        )}
        {uploadMutation.error && (
          <div className="mt-3 text-sm text-red-700 bg-red-50 dark:bg-red-900 dark:text-red-200 border-2 border-red-200 dark:border-red-700 rounded-lg px-3 py-2">
            ❌ Upload error: {(uploadMutation.error as any).response?.data?.detail || (uploadMutation.error as any).message}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Filter by group:</label>
          <select
            className="input w-72 border-2 border-slate-300 dark:border-slate-600"
            value={filterGroup || ''}
            onChange={e => setFilterGroup(e.target.value || undefined)}
          >
            <option value="">All groups</option>
            {groupsQuery.data?.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <span className="text-sm text-slate-600 dark:text-slate-400">Total: <strong>{listQuery.data?.length || 0}</strong> documents</span>
      </div>

      <div className="card border-2 border-slate-200 dark:border-slate-700 shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-600 dark:text-slate-400 border-b-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
                <th className="py-3 px-4 font-bold">📄 Filename</th>
                <th className="py-3 px-4 font-bold">📁 Group</th>
                <th className="py-3 px-4 font-bold">📌 Version</th>
                <th className="py-3 px-4 font-bold">📅 Year</th>
                <th className="py-3 px-4 font-bold">📋 Type</th>
                <th className="py-3 px-4 font-bold">✓ Status</th>
                <th className="py-3 px-4 font-bold">⚙️ Actions</th>
              </tr>
            </thead>
            <tbody>
              {listQuery.data?.map(d => (
                <tr key={d.id} className="border-b border-slate-100 dark:border-slate-700 hover:bg-blue-50 dark:hover:bg-slate-800 transition">
                  <td className="py-3 px-4">
                    <Link to={`/documents/${d.id}`} className="text-blue-600 dark:text-blue-400 hover:font-bold font-medium">
                      {d.filename}
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-slate-700 dark:text-slate-300">{d.group}</td>
                  <td className="py-3 px-4 text-slate-700 dark:text-slate-300">{d.version_label || '—'}</td>
                  <td className="py-3 px-4 text-slate-700 dark:text-slate-300">{d.year || '—'}</td>
                  <td className="py-3 px-4 uppercase text-xs text-slate-500 dark:text-slate-400 font-bold">{d.file_type}</td>
                  <td className="py-3 px-4"><StatusBadge status={d.status} /></td>
                  <td className="py-3 px-4">
                    <button
                      className="text-xs text-red-600 dark:text-red-400 hover:font-bold transition"
                      onClick={() => { if (confirm(`Delete "${d.filename}"?`)) deleteMutation.mutate(d.id) }}
                    >
                      🗑️ Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {listQuery.data?.length === 0 && <div className="text-sm text-slate-500 dark:text-slate-400 py-8 text-center">📁 No documents yet — upload one above.</div>}
      </div>
    </div>
  )
}
