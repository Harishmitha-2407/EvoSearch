import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Documents, Timeline } from '../api/client'
import { PageHeader } from '../components/Layout'

const changeColor: Record<string, string> = {
  ADDED: 'bg-emerald-100 text-emerald-700',
  REMOVED: 'bg-red-100 text-red-700',
  MODIFIED: 'bg-amber-100 text-amber-700',
  UNCHANGED: 'bg-slate-100 text-slate-500',
}

export default function TimelinePage() {
  const [group, setGroup] = useState<string | undefined>(undefined)
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const groupsQuery = useQuery({ queryKey: ['doc-groups'], queryFn: Documents.groups })
  const timelineQuery = useQuery({
    queryKey: ['timeline', group],
    queryFn: () => Timeline.get(group as string),
    enabled: !!group,
  })

  const topics = timelineQuery.data || []
  const filteredTopics = selectedTopic ? topics.filter(t => t.topic === selectedTopic) : topics

  return (
    <div>
      <PageHeader title="Evolution Timeline" subtitle="Track how each topic and requirement evolved across document versions." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Document group:</label>
          <select className="input w-full border-2 border-slate-300 focus:border-blue-500 font-medium" value={group || ''} onChange={e => { setGroup(e.target.value || undefined); setSelectedTopic(null); }}>
            <option value="">Select a group…</option>
            {groupsQuery.data?.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        {group && topics.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Filter by topic:</label>
            <select className="input w-full border-2 border-slate-300 focus:border-blue-500 font-medium" value={selectedTopic || ''} onChange={e => setSelectedTopic(e.target.value || null)}>
              <option value="">All topics ({topics.length})</option>
              {topics.map(t => <option key={t.topic} value={t.topic}>{t.topic}</option>)}
            </select>
          </div>
        )}
      </div>

      {!group && (
        <div className="card bg-gradient-to-br from-blue-50 to-slate-50 border-2 border-blue-200 text-center py-12">
          <p className="text-lg text-slate-600 mb-2">📅 Choose a document group to begin</p>
          <p className="text-sm text-slate-500">Run a comparison between two versions to generate change data.</p>
        </div>
      )}

      {group && filteredTopics.length === 0 && (
        <div className="card bg-gradient-to-br from-amber-50 to-slate-50 border-2 border-amber-200 text-center py-12">
          <p className="text-lg text-slate-600 mb-2">📊 No changes recorded</p>
          <p className="text-sm text-slate-500">Run a comparison between two versions first to generate timeline data.</p>
        </div>
      )}

      <div className="space-y-6">
        {filteredTopics.map(topic => (
          <div key={topic.topic} className="card bg-gradient-to-br from-slate-50 to-slate-100 border-2 border-slate-200 shadow-lg">
            {/* Topic Header */}
            <div className="flex items-start justify-between mb-5 pb-4 border-b-2 border-slate-300">
              <div className="flex-1">
                <h2 className="font-bold text-xl text-slate-800 mb-1">{topic.topic}</h2>
                <p className="text-sm text-slate-600">Tracked across {topic.document_count} document version(s)</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{topic.events.length}</div>
                <div className="text-xs text-slate-600">versions</div>
              </div>
            </div>

            {/* Timeline Visualization */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="text-xs font-bold text-slate-700">📈 Evolution Timeline</div>
              </div>
              
              {/* Horizontal Timeline */}
              <div className="flex overflow-x-auto gap-3 pb-4">
                {topic.events.map((ev, i) => (
                  <div key={i} className="relative flex-shrink-0">
                    {/* Timeline Connector */}
                    {i < topic.events.length - 1 && (
                      <div className="absolute left-full top-6 w-3 h-0.5 bg-gradient-to-r from-blue-400 to-slate-300"></div>
                    )}
                    
                    {/* Timeline Node */}
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold text-sm border-2 border-white shadow-lg">
                      {i + 1}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Events Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {topic.events.map((ev, i) => (
                <div key={i} className="bg-white rounded-lg border-2 border-slate-200 p-4 hover:shadow-lg hover:border-blue-300 transition">
                  {/* Event Header */}
                  <div className="flex items-start justify-between mb-3 pb-2 border-b border-slate-200">
                    <div className="flex-1">
                      <div className="text-sm font-bold text-slate-800">{ev.filename}</div>
                      <div className="text-xs text-blue-600 font-medium mt-1">
                        {ev.year ? `📅 ${ev.year}` : ''}
                        {ev.version_label ? ` (${ev.version_label})` : ''}
                        {ev.page ? ` • 📄 page ${ev.page}` : ''}
                      </div>
                    </div>
                    <div className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">
                      v{i + 1}
                    </div>
                  </div>

                  {/* Statement */}
                  <div className="mb-3">
                    <p className="text-sm text-slate-700 leading-relaxed bg-blue-50 p-2 rounded border-l-4 border-blue-400 line-clamp-4">
                      {ev.statement}
                    </p>
                  </div>

                  {/* Metadata */}
                  <div className="space-y-2 text-xs">
                    {ev.requirement_strength && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">Requirement:</span>
                        <span className={`badge px-2 py-1 font-medium rounded ${
                          ev.requirement_strength === 'mandatory' ? 'bg-red-100 text-red-700' :
                          ev.requirement_strength === 'recommended' ? 'bg-amber-100 text-amber-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {ev.requirement_strength}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Importance:</span>
                      <div className="flex items-center gap-1">
                        <div className="w-16 bg-slate-200 rounded-full h-1.5">
                          <div 
                            className="bg-gradient-to-r from-blue-400 to-blue-600 h-1.5 rounded-full" 
                            style={{width: `${ev.importance * 100}%`}}
                          ></div>
                        </div>
                        <span className="font-bold text-blue-600 w-6 text-right">{(ev.importance * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="text-slate-500 pt-1 border-t border-slate-200">
                      {new Date(ev.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
