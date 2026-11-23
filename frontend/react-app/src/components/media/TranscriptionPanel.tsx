import { useState } from 'react';
import { ArrowRight,Check,ChevronDown,Copy,FileText } from 'lucide-react';
import type { TranscriptionResult } from '../../types/api';
export function TranscriptionPanel({result,onConsult}:{result:TranscriptionResult|null;onConsult?:()=>void}){
 const [expanded,setExpanded]=useState(true);const [copied,setCopied]=useState(false);
 async function copy(){if(!result)return;try{await navigator.clipboard.writeText(result.full_text);setCopied(true);}catch{setCopied(false);}}
 const indexing=result?.indexing&&typeof result.indexing==='object'?result.indexing as Record<string,unknown>:null;
 return <section className="panel"><div className="flex items-center gap-3"><FileText size={21} style={{color:'var(--accent)'}}/><div><h2 className="section-title">Transcrição da audiência</h2><p className="muted">Texto recebido após o processamento</p></div></div>
 {!result?<div className="empty-transcription mt-6"><FileText size={30} style={{color:'var(--muted)'}}/><h3 className="mt-3 font-semibold">Sua transcrição aparecerá aqui</h3><p className="muted mt-2 max-w-sm text-center">Envie uma gravação para ler o conteúdo e iniciar uma análise com IA.</p></div>:<><div className="status-card mt-5"><p className="text-sm font-semibold">Transcrição concluída</p><p className="muted mt-1">{typeof result.segments_count === 'number' ? result.segments_count : '—'} segmentos · {typeof indexing?.chunks_count === 'number' ? indexing.chunks_count : '—'} trechos indexados</p>{typeof indexing?.status === 'string'&&<p className="muted">Indexação: {String(indexing.status)}</p>}</div>
 <div className="mt-5 flex flex-wrap items-center justify-between gap-2"><button className="inline-flex items-center gap-2 text-sm font-semibold" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}><ChevronDown size={17} className={expanded?'':'-rotate-90'}/> Transcrição completa</button><button className="btn-secondary" onClick={()=>void copy()}>{copied?<Check size={16}/>:<Copy size={16}/>} {copied?'Copiado':'Copiar texto'}</button></div>
 {expanded&&<div className="transcript-body mt-4">{result.full_text||'A API não retornou texto completo.'}</div>}
 {onConsult&&<button className="btn-primary mt-5 w-full" onClick={onConsult}>Perguntar sobre esta audiência <ArrowRight size={17}/></button>}
 </>}
 </section>;
}
