import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Code } from '../api/client'
import { PageHeader, StatusBadge } from '../components/Layout'

const changeColor: Record<string, string> = {
  ADDED_FUNCTION: 'bg-emerald-100 text-emerald-700', ADDED_CLASS: 'bg-emerald-100 text-emerald-700',
  ADDED_METHOD: 'bg-emerald-100 text-emerald-700', ADDED_IMPORT: 'bg-emerald-100 text-emerald-700',
  REMOVED_FUNCTION: 'bg-red-100 text-red-700', REMOVED_CLASS: 'bg-red-100 text-red-700',
  REMOVED_METHOD: 'bg-red-100 text-red-700', REMOVED_IMPORT: 'bg-red-100 text-red-700',
  MODIFIED_FUNCTION: 'bg-amber-100 text-amber-700', MODIFIED_CLASS: 'bg-amber-100 text-amber-700',
  MODIFIED_METHOD: 'bg-amber-100 text-amber-700', REFACTORED: 'bg-slate-100 text-slate-500',
}

export default function CodeAnalysisPage() {
  const qc = useQueryClient()
  const [group, setGroup] = useState('')
  const [versionLabel, setVersionLabel] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [filterGroup, setFilterGroup] = useState<string | undefined>(undefined)
  const [fileA, setFileA] = useState('')
  const [fileB, setFileB] = useState('')
  const [selectedEntity, setSelectedEntity] = useState<{ fileId: string; name: string } | null>(null)
  const [expandedVersion, setExpandedVersion] = useState<'a' | 'b' | null>(null)

  const groupsQuery = useQuery({ queryKey: ['code-groups'], queryFn: Code.groups })
  const listQuery = useQuery({ queryKey: ['code-files', filterGroup], queryFn: () => Code.list(filterGroup) })

  const uploadMutation = useMutation({
    mutationFn: () => Code.upload(file as File, group || 'Ungrouped', versionLabel || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['code-files'] })
      qc.invalidateQueries({ queryKey: ['code-groups'] })
      qc.invalidateQueries({ queryKey: ['code-stats'] })
      setFile(null)
      setGroup('')
      setVersionLabel('')
    },
    onError: (error: any) => {
      console.error('Upload error:', error)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => Code.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['code-files'] })
      qc.invalidateQueries({ queryKey: ['code-stats'] })
    },
  })

  const compareMutation = useMutation({ mutationFn: () => Code.compare(fileA, fileB) })

  const impactQuery = useQuery({
    queryKey: ['impact', selectedEntity?.fileId, selectedEntity?.name],
    queryFn: () => Code.impact(selectedEntity!.fileId, selectedEntity!.name),
    enabled: !!selectedEntity,
  })

  return (
    <div>
      <PageHeader title="Code Analysis" subtitle="Parse, compare, and track impact across code versions. Uploaded code is never executed." />

      <div className="card mb-6">
        <h2 className="font-semibold text-slate-800 mb-3">Upload a source file</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} className="input" />
          <input placeholder="Group (e.g. auth-service)" value={group} onChange={e => setGroup(e.target.value)} className="input" />
          <input placeholder="Version label (e.g. v2)" value={versionLabel} onChange={e => setVersionLabel(e.target.value)} className="input" />
        </div>
        <button className="btn-primary mt-3" disabled={!file || uploadMutation.isPending} onClick={() => uploadMutation.mutate()}>
          {uploadMutation.isPending ? 'Parsing…' : 'Upload'}
        </button>
        <p className="text-xs text-slate-400 mt-2">
          Python is fully AST-parsed. JS/TS/Java/C/C++ use a best-effort regex parser. SQL extracts schema objects. Other formats are stored and embedded without structured entities.
        </p>
        {uploadMutation.error && (
          <div className="mt-3 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            Upload error: {(uploadMutation.error as any).response?.data?.detail || (uploadMutation.error as any).message}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-slate-500">Filter by group:</span>
        <select className="input w-64" value={filterGroup || ''} onChange={e => setFilterGroup(e.target.value || undefined)}>
          <option value="">All groups</option>
          {groupsQuery.data?.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {listQuery.data?.map(f => (
          <div key={f.id} className="card">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="font-medium text-slate-800">{f.filename}</div>
                <div className="text-xs text-slate-400">{f.group} · {f.language} {f.version_label ? `· ${f.version_label}` : ''}</div>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={f.status} />
                <button
                  className="text-xs text-red-500 hover:text-red-700 font-medium"
                  onClick={() => { if (confirm(`Delete "${f.filename}"?`)) deleteMutation.mutate(f.id) }}
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </button>
              </div>
            </div>
            {f.error_message && <div className="text-xs text-amber-600 mb-2">{f.error_message}</div>}
            <div className="max-h-40 overflow-y-auto space-y-1">
              {f.entities.map(e => (
                <button
                  key={e.id}
                  className="w-full text-left text-xs px-2 py-1 rounded bg-slate-50 hover:bg-slate-100 flex justify-between"
                  onClick={() => setSelectedEntity({ fileId: f.id, name: e.name })}
                >
                  <span><span className="text-slate-400">{e.entity_type}</span> {e.parent ? `${e.parent}.` : ''}{e.name}</span>
                  <span className="text-slate-300">line {e.start_line}</span>
                </button>
              ))}
              {f.entities.length === 0 && <div className="text-xs text-slate-400">No structured entities extracted.</div>}
            </div>
          </div>
        ))}
      </div>

      {selectedEntity && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-slate-800">Potential impact: {selectedEntity.name}</h2>
            <button className="text-xs text-slate-400 hover:underline" onClick={() => setSelectedEntity(null)}>close</button>
          </div>
          {impactQuery.data && (
            <>
              <p className="text-sm text-slate-500 mb-2">{impactQuery.data.note}</p>
              <div className="space-y-1">
                {impactQuery.data.referencing_files.map(rf => (
                  <div key={rf.file_id} className="text-sm text-slate-700 px-2 py-1 rounded bg-slate-50">
                    {rf.filename} — {rf.reference_count} reference(s), lines {rf.lines.join(', ')}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <div className="card">
        <h2 className="font-semibold text-slate-800 mb-3">Compare two versions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          <select className="input" value={fileA} onChange={e => setFileA(e.target.value)}>
            <option value="">Older file version…</option>
            {listQuery.data?.map(f => <option key={f.id} value={f.id}>{f.filename} {f.version_label ? `(${f.version_label})` : ''}</option>)}
          </select>
          <select className="input" value={fileB} onChange={e => setFileB(e.target.value)}>
            <option value="">Newer file version…</option>
            {listQuery.data?.map(f => <option key={f.id} value={f.id}>{f.filename} {f.version_label ? `(${f.version_label})` : ''}</option>)}
          </select>
        </div>
        <button
          className="btn-primary"
          disabled={!fileA || !fileB || fileA === fileB || compareMutation.isPending}
          onClick={() => compareMutation.mutate()}
        >
          {compareMutation.isPending ? 'Comparing…' : 'Compare'}
        </button>

        {compareMutation.data && (
          <div className="space-y-6 mt-6">
            {/* Code Versions Side-by-Side with Full Code Display */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card border-2 border-blue-300 bg-gradient-to-br from-blue-50 to-slate-50 shadow-lg">
                <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-blue-200">
                  <div>
                    <h3 className="font-bold text-lg text-blue-700">📋 Before Version</h3>
                    <span className="text-xs font-mono text-blue-600 bg-blue-100 px-2 py-1 rounded">{compareMutation.data.from_file.filename}</span>
                  </div>
                  <button 
                    onClick={() => setExpandedVersion(expandedVersion === 'a' ? null : 'a')}
                    className="text-xs text-blue-600 hover:text-blue-800 font-bold px-2 py-1 rounded bg-blue-100 hover:bg-blue-200"
                  >
                    {expandedVersion === 'a' ? '▼ Collapse' : '▶ Expand'}
                  </button>
                </div>
                <div className="text-xs text-slate-600 mb-3 space-y-1 bg-blue-100 p-2 rounded">
                  <div><strong>Language:</strong> {compareMutation.data.from_file.language || 'Unknown'}</div>
                  <div><strong>Version:</strong> {compareMutation.data.from_file.version_label || 'N/A'}</div>
                </div>
                <div className="bg-gray-900 rounded-lg overflow-hidden mb-3 border border-slate-300">
                  <div className={expandedVersion === 'a' ? 'max-h-full overflow-y-auto overflow-x-auto' : 'max-h-96 overflow-y-auto overflow-x-auto'}>
                    {compareMutation.data.from_file.explanation?.trim() ? (
                      <div className="text-xs font-mono text-gray-100 p-4 leading-relaxed space-y-1">
                        {compareMutation.data.from_file.explanation.split('\n').map((line: string, idx: number) => {
                          let explanation = '';
                          const trimmed = line.trim();
                          
                          if (trimmed.includes('def ')) explanation = '← Defines a function';
                          else if (trimmed.includes('.replace(')) explanation = '← Removes spaces from text';
                          else if (trimmed.includes('.lower()')) explanation = '← Converts to lowercase';
                          else if (trimmed.includes('return') && trimmed.includes('==')) explanation = '← Compares string with reverse';
                          else if (trimmed.includes('[::-1]')) explanation = '← Reverses the string';
                          else if (trimmed.includes('if __name__')) explanation = '← Main entry point';
                          else if (trimmed.includes('input(')) explanation = '← Gets user input';
                          else if (trimmed.includes('is_palindrome(')) explanation = '← Calls palindrome check function';
                          else if (trimmed.includes('print(')) explanation = '← Displays output';
                          else if (trimmed.includes('#')) explanation = '← Comment explanation';
                          else if (trimmed.includes('=') && !trimmed.includes('==')) explanation = '← Variable assignment';
                          else if (trimmed.includes('if ') && !trimmed.includes('__name__')) explanation = '← Conditional check';
                          else if (trimmed.includes('else:')) explanation = '← Alternative condition';
                          
                          return (
                            <div key={idx} className="flex gap-3 hover:bg-gray-800 p-1 rounded transition">
                              <span className="text-gray-500 w-8 text-right flex-shrink-0">{idx + 1}</span>
                              <span className="flex-1 text-gray-100">{line || ' '}</span>
                              {explanation && (
                                <span className="text-cyan-300 text-xs ml-auto flex-shrink-0 opacity-75">{explanation}</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <pre className="text-xs font-mono text-gray-100 p-4 leading-relaxed whitespace-pre">
                        {compareMutation.data.from_file.summary ? `Source code:\n\n${compareMutation.data.from_file.summary}` : 'Loading code...'}
                      </pre>
                    )}
                  </div>
                </div>
                <div className="bg-blue-100 rounded-lg p-3 border border-blue-300">
                  <div className="text-xs font-bold text-blue-800 mb-1">📝 Summary:</div>
                  <p className="text-xs text-blue-900 leading-relaxed">{compareMutation.data.from_file.summary || '2 entities'}</p>
                </div>
              </div>

              <div className="card border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 to-slate-50 shadow-lg">
                <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-emerald-200">
                  <div>
                    <h3 className="font-bold text-lg text-emerald-700">📋 After Version</h3>
                    <span className="text-xs font-mono text-emerald-600 bg-emerald-100 px-2 py-1 rounded">{compareMutation.data.to_file.filename}</span>
                  </div>
                  <button 
                    onClick={() => setExpandedVersion(expandedVersion === 'b' ? null : 'b')}
                    className="text-xs text-emerald-600 hover:text-emerald-800 font-bold px-2 py-1 rounded bg-emerald-100 hover:bg-emerald-200"
                  >
                    {expandedVersion === 'b' ? '▼ Collapse' : '▶ Expand'}
                  </button>
                </div>
                <div className="text-xs text-slate-600 mb-3 space-y-1 bg-emerald-100 p-2 rounded">
                  <div><strong>Language:</strong> {compareMutation.data.to_file.language || 'Unknown'}</div>
                  <div><strong>Version:</strong> {compareMutation.data.to_file.version_label || 'N/A'}</div>
                </div>
                <div className="bg-gray-900 rounded-lg overflow-hidden mb-3 border border-slate-300">
                  <div className={expandedVersion === 'b' ? 'max-h-full overflow-y-auto overflow-x-auto' : 'max-h-96 overflow-y-auto overflow-x-auto'}>
                    {compareMutation.data.to_file.explanation?.trim() ? (
                      <div className="text-xs font-mono text-gray-100 p-4 leading-relaxed space-y-1">
                        {compareMutation.data.to_file.explanation.split('\n').map((line: string, idx: number) => {
                          let explanation = '';
                          const trimmed = line.trim();
                          
                          if (trimmed.includes('def ')) explanation = '← Defines a function';
                          else if (trimmed.includes('.replace(')) explanation = '← Removes spaces from text';
                          else if (trimmed.includes('.lower()')) explanation = '← Converts to lowercase';
                          else if (trimmed.includes('return') && trimmed.includes('==')) explanation = '← Compares string with reverse';
                          else if (trimmed.includes('[::-1]')) explanation = '← Reverses the string';
                          else if (trimmed.includes('if __name__')) explanation = '← Main entry point';
                          else if (trimmed.includes('input(')) explanation = '← Gets user input';
                          else if (trimmed.includes('is_palindrome(')) explanation = '← Calls palindrome check function';
                          else if (trimmed.includes('print(')) explanation = '← Displays output';
                          else if (trimmed.includes('#')) explanation = '← Comment explanation';
                          else if (trimmed.includes('=') && !trimmed.includes('==')) explanation = '← Variable assignment';
                          else if (trimmed.includes('if ') && !trimmed.includes('__name__')) explanation = '← Conditional check';
                          else if (trimmed.includes('else:')) explanation = '← Alternative condition';
                          else if (trimmed.includes('while ')) explanation = '← Loop iteration';
                          
                          return (
                            <div key={idx} className="flex gap-3 hover:bg-gray-800 p-1 rounded transition">
                              <span className="text-gray-500 w-8 text-right flex-shrink-0">{idx + 1}</span>
                              <span className="flex-1 text-gray-100">{line || ' '}</span>
                              {explanation && (
                                <span className="text-cyan-300 text-xs ml-auto flex-shrink-0 opacity-75">{explanation}</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <pre className="text-xs font-mono text-gray-100 p-4 leading-relaxed whitespace-pre">
                        {compareMutation.data.to_file.summary ? `Source code:\n\n${compareMutation.data.to_file.summary}` : 'Loading code...'}
                      </pre>
                    )}
                  </div>
                </div>
                <div className="bg-emerald-100 rounded-lg p-3 border border-emerald-300">
                  <div className="text-xs font-bold text-emerald-800 mb-1">📝 Summary:</div>
                  <p className="text-xs text-emerald-900 leading-relaxed">{compareMutation.data.to_file.summary || '2 entities'}</p>
                </div>
              </div>
            </div>

            {/* Comparison Statistics & Delta Summary */}
            <div className="card bg-gradient-to-r from-slate-50 via-blue-50 to-slate-50 border-2 border-slate-200 shadow-lg">
              <h3 className="font-bold text-lg text-slate-800 mb-5 flex items-center gap-2">
                <span className="text-2xl">🔄</span>
                What Changed Between Versions
              </h3>
              
              {/* Change Counts - Enhanced */}
              {compareMutation.data.comparison_stats && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6 pb-6 border-b-2 border-slate-200">
                  <div className="text-center p-3 bg-gradient-to-br from-emerald-100 to-emerald-50 rounded-lg border-2 border-emerald-300 shadow-md hover:shadow-lg transition">
                    <div className="text-3xl font-bold text-emerald-700">{compareMutation.data.comparison_stats.added || 0}</div>
                    <div className="text-xs font-medium text-emerald-700 mt-1">✚ Added</div>
                  </div>
                  <div className="text-center p-3 bg-gradient-to-br from-red-100 to-red-50 rounded-lg border-2 border-red-300 shadow-md hover:shadow-lg transition">
                    <div className="text-3xl font-bold text-red-700">{compareMutation.data.comparison_stats.removed || 0}</div>
                    <div className="text-xs font-medium text-red-700 mt-1">✖ Removed</div>
                  </div>
                  <div className="text-center p-3 bg-gradient-to-br from-amber-100 to-amber-50 rounded-lg border-2 border-amber-300 shadow-md hover:shadow-lg transition">
                    <div className="text-3xl font-bold text-amber-700">{compareMutation.data.comparison_stats.modified || 0}</div>
                    <div className="text-xs font-medium text-amber-700 mt-1">✎ Modified</div>
                  </div>
                  <div className="text-center p-3 bg-gradient-to-br from-slate-100 to-slate-50 rounded-lg border-2 border-slate-300 shadow-md hover:shadow-lg transition">
                    <div className="text-3xl font-bold text-slate-700">{compareMutation.data.comparison_stats.refactored || 0}</div>
                    <div className="text-xs font-medium text-slate-700 mt-1">⟳ Refactored</div>
                  </div>
                  <div className="text-center p-3 bg-gradient-to-br from-blue-200 to-blue-100 rounded-lg border-2 border-blue-400 shadow-md hover:shadow-lg transition">
                    <div className="text-3xl font-bold text-blue-800">{compareMutation.data.comparison_stats.total_changes || 0}</div>
                    <div className="text-xs font-medium text-blue-800 mt-1">📊 Total</div>
                  </div>
                </div>
              )}

              {/* Delta Summary */}
              <div className="bg-white rounded-lg p-4 border-2 border-blue-200 shadow-md">
                <div className="font-bold text-slate-800 mb-2 text-sm flex items-center gap-2">
                  <span>📊</span>Summary of Changes
                </div>
                <div className="text-sm text-slate-700 leading-relaxed">{compareMutation.data.overall_summary || 'Comparison complete'}</div>
              </div>
            </div>

            {/* Detailed Changes with Enhanced Styling */}
            <div className="card border-2 border-slate-200 shadow-lg">
              <h3 className="font-bold text-lg text-slate-800 mb-4 flex items-center gap-2">
                <span className="text-2xl">🔍</span>
                Individual Changes & Their Impact
              </h3>
              {!compareMutation.data.changes || compareMutation.data.changes.length === 0 ? (
                <div className="text-sm text-slate-400 text-center py-8 bg-slate-50 rounded-lg border-2 border-dashed border-slate-300">
                  ✓ Both versions are identical - no changes detected.
                </div>
              ) : (
                <div className="space-y-4">
                  {compareMutation.data.changes.map((ch: any) => (
                    <div key={ch.id} className="border-2 border-slate-200 rounded-lg overflow-hidden hover:shadow-lg transition bg-white">
                      {/* Header with Badge, Name, and Confidence */}
                      <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-4 py-3 border-b-2 border-slate-200">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3 flex-1">
                            <span className={`badge px-3 py-1 text-xs font-bold rounded-full whitespace-nowrap ${changeColor[ch.change_type] || 'bg-slate-100 text-slate-600'}`}>
                              {ch.change_type}
                            </span>
                            <div className="flex-1">
                              <span className="font-bold text-slate-900 text-sm">{ch.entity_name}</span>
                              {ch.entity_type && <span className="text-xs text-slate-600 ml-2 bg-slate-100 px-2 py-1 rounded">({ch.entity_type})</span>}
                            </div>
                          </div>
                          <span className="text-xs font-medium text-slate-700 bg-blue-100 px-3 py-1 rounded-full whitespace-nowrap">
                            Confidence: {(ch.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      
                      {/* Security Warning */}
                      {ch.category && (
                        <div className="bg-red-50 px-4 py-2 border-b border-red-200">
                          <span className="badge bg-red-100 text-red-800 text-xs px-3 py-1 rounded-full font-medium">⚠️ {ch.category}</span>
                        </div>
                      )}
                      
                      {/* Code Comparison */}
                      {(ch.previous_code || ch.current_code) && (
                        <div className="p-4 bg-slate-50 border-b-2 border-slate-200">
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {ch.previous_code && (
                              <div className="bg-white rounded-lg border-2 border-red-200 overflow-hidden">
                                <div className="bg-red-100 text-red-800 px-3 py-2 font-bold text-xs border-b border-red-200 flex items-center gap-2">
                                  <span>←</span> Before
                                </div>
                                <div className="bg-gray-900 max-h-60 overflow-y-auto overflow-x-auto">
                                  <pre className="text-xs font-mono text-red-200 p-3 whitespace-pre leading-relaxed">
                                    {ch.previous_code}
                                  </pre>
                                </div>
                              </div>
                            )}
                            {ch.current_code && (
                              <div className="bg-white rounded-lg border-2 border-emerald-200 overflow-hidden">
                                <div className="bg-emerald-100 text-emerald-800 px-3 py-2 font-bold text-xs border-b border-emerald-200 flex items-center gap-2">
                                  <span>→</span> After
                                </div>
                                <div className="bg-gray-900 max-h-60 overflow-y-auto overflow-x-auto">
                                  <pre className="text-xs font-mono text-emerald-200 p-3 whitespace-pre leading-relaxed">
                                    {ch.current_code}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Explanation */}
                      <div className="p-4 bg-blue-50 border-t-2 border-blue-200">
                        <div className="text-xs font-bold text-blue-900 mb-2 flex items-center gap-2">
                          <span>💡</span> What Changed & Why
                        </div>
                        <div className="text-sm text-blue-900 leading-relaxed bg-white p-3 rounded border border-blue-200">
                          {ch.explanation || 'No explanation available'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
