import { useState } from 'react';
import { ArrowRight, FileAudio2, RefreshCw, Search } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { MediaUploader } from '../components/media/MediaUploader';
import { TranscriptionPanel } from '../components/media/TranscriptionPanel';
import { useMediaHistory } from '../hooks/useMediaHistory';
import type { TranscriptionResult } from '../types/api';
export function TranscriptionPage({onConsult}:{onConsult:(filename:string)=>void}) {
 const [result,setResult] = useState<TranscriptionResult|null>(null);
 const [search,setSearch] = useState('');
 const history=useMediaHistory(); const client=useQueryClient();
 const items=(history.data ?? []).filter(item=>item.filename.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
 const filename=typeof result?.filename==='string'?result.filename:'';
 return <div className="space-y-6">
  <header><p className="eyebrow">AUDIÊNCIAS</p><h1 className="page-title">Suas gravações, organizadas</h1><p className="muted mt-2">Envie uma audiência, leia a transcrição e encontre respostas com apoio da IA.</p></header>
  <div className="grid items-start gap-6 xl:grid-cols-2">
   <div className="space-y-6">
    <MediaUploader onSuccess={value=>{setResult(value);void client.invalidateQueries({queryKey:['media-history']});}}/>
    <section className="panel"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="section-title">Gravações disponíveis</h2><p className="muted">{history.data?.length ?? 0} mídia(s) indexada(s)</p></div><button className="btn-secondary" onClick={()=>void history.refetch()} disabled={history.isFetching} aria-label="Atualizar gravações"><RefreshCw size={16} className={history.isFetching?'animate-spin':''}/> Atualizar</button></div>
     <label className="relative mt-5 block"><Search size={17} className="pointer-events-none absolute left-3 top-3.5" style={{color:'var(--muted)'}}/><span className="sr-only">Buscar gravação</span><input className="field pl-10" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Buscar pelo nome da gravação"/></label>
     {history.isPending?<p role="status" className="muted mt-4">Carregando gravações...</p>:history.isError?<div role="alert" className="mt-4"><p className="text-sm text-red-500">{history.error.message}</p><button className="btn-secondary mt-2" onClick={()=>void history.refetch()}>Tentar novamente</button></div>:items.length===0?<p className="muted mt-5">{search?'Nenhuma gravação corresponde à busca.':'Nenhuma gravação indexada. Envie a primeira acima.'}</p>:<ul className="mt-4 space-y-3">{items.map((item,i)=><li key={`${item.filename}-${i}`} className="media-item"><div className="flex min-w-0 items-start gap-3"><div className="soft-card rounded-xl p-2"><FileAudio2 size={20}/></div><div className="min-w-0 flex-1"><p className="break-words text-sm font-semibold">{item.filename}</p><p className="muted mt-1">{item.chunks_count} trechos indexados</p><button className="mt-3 inline-flex items-center gap-2 text-sm font-semibold" style={{color:'var(--accent)'}} onClick={()=>onConsult(item.filename)}>Perguntar sobre esta gravação <ArrowRight size={15}/></button></div></div></li>)}</ul>}
    </section>
   </div>
   <TranscriptionPanel result={result} onConsult={filename?()=>onConsult(filename):undefined}/>
  </div>
 </div>;
}
