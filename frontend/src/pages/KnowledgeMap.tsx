import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Documents, Timeline } from '../api/client'
import { PageHeader } from '../components/Layout'

export default function KnowledgeMapPage() {
  const [group, setGroup] = useState<string | undefined>(undefined)
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const groupsQuery = useQuery({ queryKey: ['doc-groups'], queryFn: Documents.groups })
  const mapQuery = useQuery({
    queryKey: ['knowledge-map', group],
    queryFn: () => Timeline.knowledgeMap(group as string),
    enabled: !!group,
  })
  const timelineQuery = useQuery({
    queryKey: ['timeline', group],
    queryFn: () => Timeline.get(group as string),
    enabled: !!group && !!selectedTopic,
  })

  const topics = mapQuery.data?.nodes.filter(n => n.type === 'topic') ?? []
  const docs = mapQuery.data?.nodes.filter(n => n.type === 'document') ?? []
  const docsById = Object.fromEntries(docs.map(n => [n.id, n]))
  const edges = mapQuery.data?.edges ?? []

  const selectedTopicData = selectedTopic ? topics.find(t => t.id === selectedTopic) : null
  const selectedTopicTimeline = selectedTopic && timelineQuery.data 
    ? timelineQuery.data.find(t => t.topic === selectedTopic?.replace('topic:', ''))?.events ?? []
    : []

  // Calculate node positions for network visualization (force-directed simulation approximation)
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}
    const radius = 150
    const centerX = 200, centerY = 200
    
    // Position topics in circle
    topics.forEach((t, i) => {
      const angle = (i / Math.max(topics.length, 1)) * Math.PI * 2
      positions[t.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      }
    })
    
    // Position docs clustered by connected topic
    docs.forEach((d, i) => {
      const connectedTopic = edges.find(e => e.target === d.id)?.source
      if (connectedTopic && positions[connectedTopic]) {
        const topicPos = positions[connectedTopic]
        const angle = (i / Math.max(docs.length, 1)) * Math.PI * 2
        positions[d.id] = {
          x: topicPos.x + 60 * Math.cos(angle),
          y: topicPos.y + 60 * Math.sin(angle)
        }
      } else {
        positions[d.id] = { x: centerX, y: centerY + i * 40 }
      }
    })
    return positions
  }, [topics, docs, edges])

  const svgWidth = 500, svgHeight = 450

  return (
    <div>
      <PageHeader title="Knowledge Map" subtitle="Visual map of how topics and documents connect. Click nodes to explore details." />

      <div className="flex items-center gap-4 mb-8">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Document group:</span>
        <select className="input w-72 border-2 border-slate-300 dark:border-slate-600 focus:border-blue-500 dark:focus:border-blue-400 font-medium" value={group || ''} onChange={e => { setGroup(e.target.value || undefined); setSelectedTopic(null) }}>
          <option value="">Select a group…</option>
          {groupsQuery.data?.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>

      {!group && <div className="text-center py-12 text-slate-500 dark:text-slate-400">📁 Choose a document group to see its knowledge map.</div>}
      {group && topics.length === 0 && <div className="text-center py-12 text-slate-500 dark:text-slate-400">📊 No topics/claims found for this group yet.</div>}

      {group && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Interactive Network Map */}
          <div className="lg:col-span-2">
            <div className="card bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg">
              <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
                <span className="text-2xl">🗺️</span>
                Knowledge Network
                <span className="text-sm font-normal text-slate-500 dark:text-slate-400 ml-auto">
                  {topics.length} topics • {docs.length} documents
                </span>
              </h3>
              <div className="bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-700 dark:to-slate-800 rounded-xl p-4 border-2 border-slate-200 dark:border-slate-600 overflow-x-auto shadow-inner">
                <svg width={svgWidth} height={svgHeight} className="mx-auto filter drop-shadow-sm">
                  {/* Connection Lines */}
                  {edges.map((edge, idx) => {
                    const sourcePos = nodePositions[edge.source]
                    const targetPos = nodePositions[edge.target]
                    return sourcePos && targetPos ? (
                      <line
                        key={`edge-${idx}`}
                        x1={sourcePos.x} y1={sourcePos.y}
                        x2={targetPos.x} y2={targetPos.y}
                        stroke="#94a3b8" strokeWidth="2" opacity="0.4"
                        strokeDasharray="4"
                      />
                    ) : null
                  })}
                  
                  {/* Topic Nodes (Blue) */}
                  {topics.map(topic => {
                    const pos = nodePositions[topic.id]
                    const connectedDocCount = edges.filter(e => e.source === topic.id).length
                    const isSelected = selectedTopic === topic.id
                    return pos ? (
                      <g key={topic.id}>
                        <circle
                          cx={pos.x} cy={pos.y} r={isSelected ? 32 : 26}
                          fill={isSelected ? '#2563eb' : '#3b82f6'}
                          opacity={isSelected ? 1 : 0.85}
                          className="cursor-pointer hover:opacity-100 transition duration-200 drop-shadow-md"
                          onClick={() => setSelectedTopic(isSelected ? null : topic.id)}
                          style={{filter: isSelected ? 'drop-shadow(0 4px 8px rgba(37, 99, 235, 0.4))' : 'drop-shadow(0 2px 4px rgba(59, 130, 246, 0.2))'}}
                        />
                        <text
                          x={pos.x} y={pos.y}
                          textAnchor="middle" dominantBaseline="middle"
                          fontSize="12" fontWeight="bold" fill="white"
                          className="cursor-pointer pointer-events-none select-none drop-shadow-md"
                        >
                          {connectedDocCount}
                        </text>
                      </g>
                    ) : null
                  })}
                  
                  {/* Document Nodes (Green) */}
                  {docs.map(doc => {
                    const pos = nodePositions[doc.id]
                    return pos ? (
                      <circle
                        key={doc.id}
                        cx={pos.x} cy={pos.y} r="16"
                        fill="#10b981" opacity="0.8"
                        className="cursor-pointer hover:opacity-100 transition duration-200 drop-shadow-md"
                        style={{filter: 'drop-shadow(0 2px 4px rgba(16, 185, 129, 0.3))'}}
                      />
                    ) : null
                  })}
                </svg>
              </div>
              <div className="text-sm text-slate-600 dark:text-slate-400 mt-4 flex gap-6 bg-slate-100 dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
                <span className="flex items-center gap-2">
                  <span className="inline-block w-4 h-4 rounded-full bg-blue-500"></span>
                  <span>Topics (clickable)</span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="inline-block w-4 h-4 rounded-full bg-green-500"></span>
                  <span>Documents</span>
                </span>
              </div>
            </div>
          </div>

          {/* Details Panel */}
          <div>
            {selectedTopicData ? (
              <div className="card sticky top-4 max-h-96 overflow-y-auto bg-gradient-to-br from-blue-50 to-slate-50 dark:from-slate-800 dark:to-slate-900 border-2 border-blue-200 dark:border-slate-700 shadow-lg">
                <button
                  onClick={() => setSelectedTopic(null)}
                  className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 float-right font-bold"
                >
                  ✕
                </button>
                <h3 className="font-bold text-lg text-blue-600 dark:text-blue-400 mb-4 pr-6">{selectedTopicData.label}</h3>
                
                <div className="space-y-5">
                  <div>
                    <div className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
                      <span className="text-lg">📄</span>
                      Referenced in {edges.filter(e => e.source === selectedTopic).length} document(s)
                    </div>
                    <div className="space-y-2">
                      {edges
                        .filter(e => e.source === selectedTopic)
                        .map(e => docsById[e.target])
                        .filter(Boolean)
                        .map(doc => (
                          <div key={doc.id} className="text-sm p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900 border-2 border-emerald-200 dark:border-emerald-700 hover:bg-emerald-100 dark:hover:bg-emerald-800 transition font-medium text-emerald-900 dark:text-emerald-100">
                            {doc.label}
                          </div>
                        ))}
                    </div>
                  </div>

                  {selectedTopicTimeline.length > 0 && (
                    <div>
                      <div className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
                        <span className="text-lg">📈</span>
                        Evolution Timeline
                      </div>
                      <div className="space-y-2">
                        {selectedTopicTimeline.slice(0, 5).map((event, i) => (
                          <div key={i} className="text-sm p-3 rounded-lg bg-slate-100 dark:bg-slate-700 border-2 border-slate-300 dark:border-slate-600 hover:bg-slate-200 dark:hover:bg-slate-600 transition">
                            <div className="font-bold text-slate-800 dark:text-slate-200">{event.filename}</div>
                            <div className="text-slate-600 dark:text-slate-400 line-clamp-2 mt-1 text-xs">{event.statement}</div>
                          </div>
                        ))}
                        {selectedTopicTimeline.length > 5 && (
                          <div className="text-xs text-slate-500 dark:text-slate-400 text-center pt-2 font-medium">+{selectedTopicTimeline.length - 5} more versions</div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="card text-center py-16 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 border-2 border-slate-200 dark:border-slate-700 shadow-lg">
                <p className="text-lg text-slate-500 dark:text-slate-400 font-medium">👆 Click a blue node</p>
                <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">to see topic details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
