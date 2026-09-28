export interface Document {
  id: string
  filename: string
  file_type: string
  size_bytes: number
  group: string
  version_label?: string | null
  year?: number | null
  status: 'pending' | 'processing' | 'ready' | 'failed'
  error_message?: string | null
  short_summary?: string | null
  detailed_summary?: string | null
  key_topics: string[]
  document_type_guess?: string | null
  created_at: string
}

export interface Claim {
  id: string
  topic: string
  original_statement: string
  normalized_statement: string
  requirement_strength?: string | null
  scope?: string | null
  importance: number
  page?: number | null
}

export interface Suggestion {
  category: string
  description: string
  evidence?: string | null
  location?: string | null
  confidence: number
}

export interface SearchResultItem {
  chunk_id: string
  document_id: string
  document_filename: string
  text: string
  similarity: number
  page?: number | null
  section?: string | null
  group?: string | null
  year?: number | null
}

export interface SearchResponse {
  query: string
  results: SearchResultItem[]
  insufficient_evidence: boolean
}

export interface ChatSource {
  document_id: string
  document_filename: string
  chunk_id: string
  page?: number | null
  similarity: number
}

export interface ChatResponse {
  session_id: string
  answer: string
  confidence: number
  sources: ChatSource[]
  insufficient_evidence: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  confidence?: number | null
  created_at?: string
}

export interface Change {
  id: string
  topic: string
  change_type: string
  semantic_change?: string | null
  previous_text?: string | null
  current_text?: string | null
  explanation?: string | null
  confidence: number
  from_year?: number | null
  to_year?: number | null
  from_version_label?: string | null
  to_version_label?: string | null
}

export interface ComparisonResult {
  changes: Change[]
  evolution_score: { score: number; factors: Record<string, number> }
  document_a: { id: string; filename: string; version_label?: string; year?: number }
  document_b: { id: string; filename: string; version_label?: string; year?: number }
}

export interface TimelineEvent {
  document_id: string
  filename: string
  year?: number | null
  version_label?: string | null
  created_at: string
  topic: string
  statement: string
  importance: number
  page?: number | null
  requirement_strength?: string | null
}

export interface TimelineTopic {
  topic: string
  events: TimelineEvent[]
  document_count: number
}

export interface KnowledgeMapNode {
  id: string
  label: string
  type: 'topic' | 'document'
}
export interface KnowledgeMapEdge {
  source: string
  target: string
}
export interface KnowledgeMap {
  group: string
  nodes: KnowledgeMapNode[]
  edges: KnowledgeMapEdge[]
}

export interface CodeEntity {
  id: string
  entity_type: string
  name: string
  parent?: string | null
  start_line?: number | null
  end_line?: number | null
  signature?: string | null
  docstring?: string | null
}

export interface CodeFile {
  id: string
  filename: string
  language: string
  group: string
  version_label?: string | null
  status: string
  error_message?: string | null
  entities: CodeEntity[]
}

export interface CodeChange {
  id: string
  change_type: string
  entity_name: string
  entity_type?: string | null
  previous_code?: string | null
  current_code?: string | null
  explanation?: string | null
  category?: string | null
  confidence: number
}

export interface CodeFileSummary {
  total_entities: number
  by_type: Record<string, number>
  key_metrics: Record<string, number | string>
  overview: string
}

export interface CodeFileWithSummary {
  id: string
  filename: string
  language: string
  version_label?: string | null
  summary: string
  explanation: string
}

export interface ComparisonStats {
  added: number
  removed: number
  modified: number
  refactored: number
  total_changes: number
}

export interface CodeComparisonResult {
  changes: CodeChange[]
  from_file: CodeFileWithSummary
  to_file: CodeFileWithSummary
  comparison_stats: ComparisonStats
  overall_summary: string
}

export interface ImpactResult {
  entity_name: string
  referencing_files: Array<{ file_id: string; filename: string; reference_count: number; lines: number[] }>
  note: string
}

export interface HealthStatus {
  status: string
  database: string
  vector_store: string
  llm_provider: string
  embedding_model: string
}
