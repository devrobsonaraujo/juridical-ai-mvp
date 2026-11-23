export interface MediaHistoryItem { filename: string; chunks_count: number }
export interface TranscriptionResult { full_text: string; segments_count: number; [key: string]: unknown }
export interface RagSource { start?: number; audio_filename?: string; text?: string }
export interface RagResult { answer: string; sources: RagSource[] }
export interface RagQuery { question: string; k: number; audio_filter: string | null }
export type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string; sources?: RagSource[]; error?: boolean };
