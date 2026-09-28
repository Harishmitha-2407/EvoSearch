import axios from 'axios'
import type {
  Document, Claim, Suggestion, SearchResponse, ChatResponse, ChatMessage,
  ComparisonResult, TimelineTopic, KnowledgeMap, CodeFile, CodeChange,
  ImpactResult, HealthStatus, CodeComparisonResult,
} from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: `${API_URL}/api` })

// Add authorization token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const Health = {
  get: () => api.get<HealthStatus>('/health').then(r => r.data),
}

export const Documents = {
  list: (group?: string) => api.get<Document[]>('/documents', { params: { group } }).then(r => r.data),
  groups: () => api.get<string[]>('/documents/groups').then(r => r.data),
  stats: () => api.get<{ total_documents: number; total_groups: number; total_claims: number; total_changes: number; failed_documents: number }>('/documents/stats/summary').then(r => r.data),
  get: (id: string) => api.get<Document>(`/documents/${id}`).then(r => r.data),
  claims: (id: string) => api.get<Claim[]>(`/documents/${id}/claims`).then(r => r.data),
  suggestions: (id: string) => api.get<Suggestion[]>(`/documents/${id}/suggestions`).then(r => r.data),
  remove: (id: string) => api.delete(`/documents/${id}`).then(r => r.data),
  upload: (file: File, group: string, versionLabel?: string, year?: number) => {
    const form = new FormData()
    form.append('file', file)
    form.append('group', group)
    if (versionLabel) form.append('version_label', versionLabel)
    if (year) form.append('year', String(year))
    return api.post<Document>('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
}

export const Search = {
  query: (query: string, top_k = 8, filters?: Record<string, unknown>) =>
    api.post<SearchResponse>('/search', { query, top_k, filters }).then(r => r.data),
}

export const Chat = {
  send: (question: string, sessionId?: string, documentId?: string, group?: string) =>
    api.post<ChatResponse>('/chat', {
      question, session_id: sessionId, document_id: documentId, group,
    }).then(r => r.data),
  history: (sessionId: string) => api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`).then(r => r.data),
  sessions: () => api.get('/chat/sessions').then(r => r.data),
}

export const Comparison = {
  compare: (documentIdA: string, documentIdB: string) =>
    api.post<ComparisonResult>('/comparison/documents', {
      document_id_a: documentIdA, document_id_b: documentIdB,
    }).then(r => r.data),
}

export const Timeline = {
  get: (group: string) => api.get<TimelineTopic[]>(`/timeline/${encodeURIComponent(group)}`).then(r => r.data),
  knowledgeMap: (group: string) => api.get<KnowledgeMap>(`/timeline/${encodeURIComponent(group)}/knowledge-map`).then(r => r.data),
}

export const Code = {
  list: (group?: string) => api.get<CodeFile[]>('/code/files', { params: { group } }).then(r => r.data),
  groups: () => api.get<string[]>('/code/groups').then(r => r.data),
  stats: () => api.get<{ total_files: number; total_entities: number; total_changes: number; total_groups: number }>('/code/stats/summary').then(r => r.data),
  get: (id: string) => api.get<CodeFile>(`/code/files/${id}`).then(r => r.data),
  suggestions: (id: string) => api.get<Suggestion[]>(`/code/files/${id}/suggestions`).then(r => r.data),
  upload: (file: File, group: string, versionLabel?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('group', group)
    if (versionLabel) form.append('version_label', versionLabel)
    return api.post<CodeFile>('/code/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  delete: (id: string) => api.delete(`/code/files/${id}`).then(r => r.data),
  compare: (fromFileId: string, toFileId: string) =>
    api.post<CodeComparisonResult>('/code/compare', {
      from_file_id: fromFileId, to_file_id: toFileId,
    }).then(r => r.data),
  impact: (fileId: string, entityName: string) =>
    api.get<ImpactResult>(`/code/files/${fileId}/impact/${encodeURIComponent(entityName)}`).then(r => r.data),
}

export default api
