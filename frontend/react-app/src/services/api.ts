
import { supabase } from '../lib/supabase';

import type {
  MediaHistoryItem,
  RagQuery,
  RagResult,
  RagSource,
  TranscriptionResult,
} from '../types/api';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  'https://juridical-ai-mvp.onrender.com'
).replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function record(value: unknown): Record<string, unknown> {
  return value &&
    typeof value === 'object' &&
    !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function string(
  value: unknown,
  fallback = ''
): string {
  if (typeof value === 'string') return value;
  if (value == null) return fallback;
  return String(value);
}

function number(value: unknown): number {
  const converted = Number(value);
  return Number.isFinite(converted) ? converted : 0;
}

async function getAccessToken(): Promise<string> {
  const { data, error } = await supabase.auth.getSession();

  if (error || !data.session?.access_token) {
    throw new ApiError(
      'Sua sessão expirou. Faça login novamente.',
      401
    );
  }

  return data.session.access_token;
}

async function request(
  path: string,
  init: RequestInit = {},
  timeout = 15000
): Promise<unknown> {
  const accessToken = await getAccessToken();

  const controller = new AbortController();

  const timer = setTimeout(() => {
    controller.abort();
  }, timeout);

  try {
    const headers = new Headers(init.headers);

    headers.set(
      'Authorization',
      `Bearer ${accessToken}`
    );

    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        ...init,
        headers,
        signal: controller.signal,
      }
    );

    const raw = await response.text();

    let data: unknown;

    try {
      data = raw ? JSON.parse(raw) : {};
    } catch {
      data = { detail: raw };
    }

    if (!response.ok) {
      const info = record(data);
      const detail = info.detail ?? info.message;

      if (response.status === 401) {
        throw new ApiError(
          'Sua sessão é inválida ou expirou. ' +
          'Faça login novamente.',
          401
        );
      }

      if (response.status === 403) {
        throw new ApiError(
          'Você não tem permissão para realizar esta operação.',
          403
        );
      }

      throw new ApiError(
        `Erro HTTP ${response.status}: ${
          typeof detail === 'string'
            ? detail.slice(0, 350)
            : 'Não foi possível concluir a solicitação.'
        }`,
        response.status
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (controller.signal.aborted) {
      throw new ApiError(
        `Tempo limite excedido (${Math.round(
          timeout / 1000
        )} segundos). O processamento pode continuar ` +
        'no servidor; confira o histórico antes de reenviar.'
      );
    }

    throw new ApiError(
      'Não foi possível conectar à API. ' +
      'Verifique a rede, a URL do backend e o CORS.'
    );
  } finally {
    clearTimeout(timer);
  }
}

export const api = {
  async history(): Promise<MediaHistoryItem[]> {
    const data = await request(
      '/api/v1/audio/history',
      {},
      5000
    );

    const obj = record(data);

    const items = Array.isArray(data)
      ? data
      : Array.isArray(obj.history)
        ? obj.history
        : [];

    return items
      .map((value: unknown) => {
        const item = record(value);

        return {
          filename: string(
            item.filename ??
            item.audio_filename ??
            item.name
          ),
          chunks_count: number(
            item.chunks_count ??
            item.chunks ??
            item.segments_count
          ),
        };
      })
      .filter(
        (item: MediaHistoryItem) =>
          Boolean(item.filename)
      );
  },

  async transcribe(
    file: File
  ): Promise<TranscriptionResult> {
    const form = new FormData();

    form.append('file', file);

    const data = record(
      await request(
        '/api/v1/audio/transcribe',
        {
          method: 'POST',
          body: form,
        },
        600000
      )
    );

    const nested = record(
      data.data ?? data.result
    );

    const value = Object.keys(nested).length
      ? nested
      : data;

    return {
      ...value,
      full_text: string(
        value.full_text ??
        value.transcription ??
        value.text
      ),
      segments_count: number(
        value.segments_count ??
        (
          Array.isArray(value.segments)
            ? value.segments.length
            : 0
        )
      ),
    };
  },

  async query(
    payload: RagQuery
  ): Promise<RagResult> {
    const data = record(
      await request(
        '/api/v1/rag/query',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        },
        60000
      )
    );

    const nested = record(
      data.data ?? data.result
    );

    const value = Object.keys(nested).length
      ? nested
      : data;

    const rawSources = Array.isArray(value.sources)
      ? value.sources
      : Array.isArray(value.references)
        ? value.references
        : [];

    const sources: RagSource[] = rawSources.map(
      (source: unknown) => {
        const item = record(source);
        const metadata = record(item.metadata);

        return {
          start: number(
            item.start ??
            item.start_time ??
            metadata.start
          ),
          audio_filename: string(
            item.audio_filename ??
            item.filename ??
            metadata.audio_filename ??
            metadata.filename,
            'Mídia'
          ),
          text: string(
            item.text ??
            item.content ??
            item.page_content
          ),
        };
      }
    );

    return {
      answer: string(
        value.answer ?? value.response,
        'Sem resposta.'
      ),
      sources,
    };
  },
};
