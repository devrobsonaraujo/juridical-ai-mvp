import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Check, Copy, FileAudio2, LoaderCircle, MessageSquareText, Send, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { api } from '../services/api';
import { useMediaHistory } from '../hooks/useMediaHistory';
import { SourcesList } from '../components/rag/SourcesList';
import type { ChatMessage } from '../types/api';

const suggestions = [
  'Resuma os principais pontos desta gravação.',
  'Quais trechos merecem uma revisão mais cuidadosa?',
  'Organize os fatos mencionados em ordem cronológica.',
  'Quais informações são relevantes e onde aparecem na gravação?',
];

interface RagPageProps {
  selectedMedia: string;
  onSelectMedia: (filename: string) => void;
}

export function RagPage({ selectedMedia, onSelectMedia }: RagPageProps) {
  const history = useMediaHistory();
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scopeRef = useRef(selectedMedia);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [messages, busy]);

  // A troca de mídia inicia uma conversa nova para não misturar fontes de gravações distintas.
  function changeMedia(filename: string) {
    if (busy) return;
    scopeRef.current = filename;
    onSelectMedia(filename);
    setMessages([]);
    setQuestion('');
    setCopiedId(null);
  }

  // A seleção pode mudar ao clicar em "Perguntar sobre esta gravação" na outra página.
  useEffect(() => {
    if (scopeRef.current !== selectedMedia) {
      scopeRef.current = selectedMedia;
      setMessages([]);
      setQuestion('');
      setCopiedId(null);
    }
  }, [selectedMedia]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const text = question.trim();
    if (!text || busy) return;
    const mediaAtRequest = selectedMedia;
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'user', content: text }]);
    setQuestion('');
    setBusy(true);
    try {
      const result = await api.query({ question: text, k: 8, audio_filter: mediaAtRequest || null });
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: result.answer, sources: result.sources }]);
    } catch (error) {
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: error instanceof Error ? error.message : 'Não foi possível concluir a consulta.', error: true }]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  async function copyAnswer(message: ChatMessage) {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopiedId(message.id);
    } catch {
      setCopiedId(null);
    }
  }

  function suggest(text: string) {
    setQuestion(text);
    inputRef.current?.focus();
  }

  return (
    <div className="rag-page mx-auto w-full max-w-6xl min-w-0">
      <header className="mb-6">
        <p className="eyebrow">ANÁLISE DE AUDIÊNCIAS</p>
        <h1 className="page-title">Assistente jurídico</h1>
        <p className="muted mt-2">Pergunte sobre uma gravação e confira as fontes antes de utilizar as informações.</p>
      </header>

      <section className="panel mb-4" aria-label="Selecionar gravação">
        <div className="flex items-center gap-2"><FileAudio2 size={18} style={{ color: 'var(--accent)' }} /><label className="label mb-0" htmlFor="filter">Gravação em análise</label></div>
        <select id="filter" className="field mt-3" value={selectedMedia} onChange={event => changeMedia(event.target.value)} disabled={busy}>
          <option value="">Todas as gravações</option>
          {history.data?.map((item, index) => <option key={`${item.filename}-${index}`} value={item.filename}>{item.filename}</option>)}
          {selectedMedia && !history.data?.some(item => item.filename === selectedMedia) && <option value={selectedMedia}>{selectedMedia}</option>}
        </select>
        <p className="muted mt-2">{selectedMedia ? 'As próximas perguntas serão direcionadas a esta gravação.' : 'As próximas perguntas poderão consultar todas as mídias indexadas.'}</p>
        {history.isError && <p role="alert" className="muted mt-2">Não foi possível carregar a lista de gravações: {history.error.message}</p>}
      </section>

      <section className="panel rag-chat" aria-label="Conversa com o assistente">
        <div className="rag-messages" role="log" aria-label="Mensagens da conversa" aria-live="polite">
          {messages.length === 0 && <div className="rag-empty">
            <span className="rag-empty-icon"><Sparkles size={26} aria-hidden="true" /></span>
            <h2 className="mt-4 text-xl font-semibold">O que você gostaria de analisar?</h2>
            <p className="muted mt-2 max-w-md text-center">Comece com uma pergunta ou escolha uma sugestão. As respostas devem ser conferidas nas gravações originais.</p>
            <div className="rag-suggestions mt-6">
              {suggestions.map(item => <button key={item} type="button" className="rag-suggestion" onClick={() => suggest(item)}>{item}</button>)}
            </div>
          </div>}
          {messages.map(message => <article key={message.id} className={`rag-message ${message.role === 'user' ? 'rag-user' : 'rag-assistant'} ${message.error ? 'rag-error' : ''}`}>
            <div className="rag-bubble">
              {message.role === 'assistant' && <div className="rag-speaker"><MessageSquareText size={15} aria-hidden="true" /> Assistente jurídico</div>}
              <div className="markdown break-words"><ReactMarkdown>{message.content}</ReactMarkdown></div>
              {message.sources && <SourcesList sources={message.sources} />}
              {message.role === 'assistant' && !message.error && <button type="button" className="rag-copy" onClick={() => void copyAnswer(message)} aria-label="Copiar resposta">{copiedId === message.id ? <Check size={15} /> : <Copy size={15} />}{copiedId === message.id ? 'Copiado' : 'Copiar resposta'}</button>}
            </div>
          </article>)}
          {busy && <div role="status" className="rag-processing"><LoaderCircle size={17} className="animate-spin" aria-hidden="true" /> Consultando as gravações e preparando a resposta...</div>}
          <div ref={bottomRef} />
        </div>
        <form className="rag-composer" onSubmit={event => void submit(event)}>
          <label htmlFor="question" className="sr-only">Sua pergunta sobre a audiência</label>
          <textarea id="question" ref={inputRef} className="field rag-input" rows={2} value={question} onChange={event => setQuestion(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); void submit(); } }} placeholder="Pergunte sobre fatos, depoimentos ou trechos da gravação..." disabled={busy} />
          <button className="btn-primary rag-send" type="submit" disabled={busy || !question.trim()} aria-label="Enviar pergunta"><Send size={18} /><span className="hidden sm:inline">Enviar</span></button>
        </form>
        <p className="muted mt-2 text-xs">Enter envia · Shift + Enter quebra linha. Verifique as respostas e suas fontes.</p>
      </section>
    </div>
  );
}
