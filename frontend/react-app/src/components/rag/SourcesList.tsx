import { useState } from 'react';
import { ChevronDown, Clock3, FileAudio2 } from 'lucide-react';
import type { RagSource } from '../../types/api';

export function formatTimestamp(value?: number) {
  const seconds = Math.max(0, Math.floor(Number(value) || 0));
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
}

export function SourcesList({ sources }: { sources: RagSource[] }) {
  const [expanded, setExpanded] = useState(false);
  if (!sources.length) return null;
  return (
    <section className="sources-box mt-4" aria-label="Fontes da resposta">
      <button type="button" className="sources-toggle" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>
        <span className="flex min-w-0 items-center gap-2"><FileAudio2 size={17} aria-hidden="true" /> Fontes consultadas <span className="source-count">{sources.length}</span></span>
        <ChevronDown size={17} className={expanded ? 'rotate-180' : ''} aria-hidden="true" />
      </button>
      {expanded && <ol className="mt-3 space-y-3">
        {sources.map((source, index) => (
          <li key={`${source.audio_filename ?? 'media'}-${source.start ?? 0}-${index}`} className="source-entry">
            <div className="flex items-center gap-2 text-xs font-semibold"><Clock3 size={14} aria-hidden="true" /><span>[{formatTimestamp(source.start)}]</span></div>
            <p className="mt-1 break-all text-xs font-semibold">{source.audio_filename || 'Mídia não identificada'}</p>
            <p className="muted mt-2 whitespace-pre-wrap break-words">{source.text || 'Trecho não informado pela API.'}</p>
          </li>
        ))}
      </ol>}
    </section>
  );
}
