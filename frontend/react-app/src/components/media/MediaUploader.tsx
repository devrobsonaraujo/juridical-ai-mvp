import { useEffect,useRef,useState,type ChangeEvent,type DragEvent } from 'react';
import { FileUp,LoaderCircle,FileAudio2,X,CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import type { TranscriptionResult } from '../../types/api';
const allowed=['mp4','mkv','avi','mov','mp3','wav','m4a'];
export function MediaUploader({onSuccess}:{onSuccess:(result:TranscriptionResult)=>void}) {
 const [file,setFile]=useState<File|null>(null); const [url,setUrl]=useState(''); const [dragging,setDragging]=useState(false); const [busy,setBusy]=useState(false); const [elapsed,setElapsed]=useState(0); const [error,setError]=useState(''); const [success,setSuccess]=useState(false); const input=useRef<HTMLInputElement>(null);
 useEffect(()=>{if(!file){setUrl('');return;}const next=URL.createObjectURL(file);setUrl(next);return()=>URL.revokeObjectURL(next);},[file]);
 useEffect(()=>{if(!busy)return;const id=window.setInterval(()=>setElapsed(s=>s+1),1000);return()=>window.clearInterval(id);},[busy]);
 function choose(next:File|null){setError('');setSuccess(false);if(next&&!allowed.includes(next.name.split('.').pop()?.toLowerCase()??'')){setFile(null);setError('Formato não suportado. Escolha MP4, MKV, AVI, MOV, MP3, WAV ou M4A.');return;}setFile(next);}
 function change(e:ChangeEvent<HTMLInputElement>){choose(e.target.files?.[0]??null);e.target.value='';}
 function drop(e:DragEvent<HTMLElement>){e.preventDefault();setDragging(false);if(!busy)choose(e.dataTransfer.files?.[0]??null);}
 async function send(){if(!file||busy)return;setBusy(true);setElapsed(0);setError('');setSuccess(false);try{const result=await api.transcribe(file);onSuccess(result);setSuccess(true);}catch(e){setError(e instanceof Error?e.message:'Não foi possível processar a gravação.');}finally{setBusy(false);}}
 const video=file&&['mp4','mkv','avi','mov'].includes(file.name.split('.').pop()?.toLowerCase()??'');
 const duration=`${String(Math.floor(elapsed/60)).padStart(2,'0')}:${String(elapsed%60).padStart(2,'0')}`;
 return <section className="panel"><h2 className="section-title">Enviar nova gravação</h2><p className="muted mb-5 mt-1">Selecione um áudio ou vídeo para transcrever e preparar para consultas.</p>
  <div onDragOver={e=>{e.preventDefault();if(!busy)setDragging(true);}} onDragLeave={e=>{e.preventDefault();setDragging(false);}} onDrop={drop} className={`upload-zone ${dragging?'upload-zone-active':''}`}>
   <FileUp size={30} style={{color:'var(--accent)'}}/><p className="mt-3 text-sm font-semibold">Arraste uma gravação até aqui</p><p className="muted mt-1">ou escolha um arquivo do dispositivo</p><button type="button" className="btn-secondary mt-4" disabled={busy} onClick={()=>input.current?.click()}>Selecionar arquivo</button><p className="mt-3 text-xs" style={{color:'var(--muted)'}}>MP4, MKV, AVI, MOV, MP3, WAV, M4A</p>
   <input ref={input} type="file" accept=".mp4,.mkv,.avi,.mov,.mp3,.wav,.m4a" onChange={change} disabled={busy} className="sr-only" aria-label="Selecionar arquivo de áudio ou vídeo"/>
  </div>
  {file&&<div className="media-item mt-4"><div className="flex items-start gap-3"><FileAudio2 className="mt-0.5 shrink-0" size={20}/><div className="min-w-0 flex-1"><p className="break-words text-sm font-semibold">{file.name}</p><p className="muted">{(file.size/1048576).toFixed(2)} MB</p></div><button disabled={busy} className="icon-button shrink-0" aria-label="Remover arquivo" onClick={()=>choose(null)}><X size={18}/></button></div>{video?<video controls src={url} className="mt-4 max-h-72 w-full rounded-lg bg-black"/>:<audio controls src={url} className="mt-4 w-full"/>}<p className="mt-2 text-xs" style={{color:'var(--muted)'}}>A reprodução depende do formato e dos codecs suportados pelo navegador.</p></div>}
  {busy&&<div role="status" aria-live="polite" className="status-card mt-4"><div className="flex items-center gap-2 font-semibold"><LoaderCircle className="animate-spin" size={17}/> Processando gravação · {duration}</div><p className="muted mt-2">Estamos enviando, transcrevendo e indexando. Mantenha esta aba aberta. Arquivos longos podem levar vários minutos.</p></div>}
  {success&&<p role="status" className="mt-4 flex items-center gap-2 text-sm" style={{color:'var(--accent)'}}><CheckCircle2 size={18}/> Transcrição recebida. Confira o resultado ao lado.</p>}
  {error&&<div role="alert" className="mt-4 rounded-xl border border-red-400 p-3 text-sm text-red-500">{error}<p className="mt-2">Se houve timeout, consulte o histórico antes de reenviar para evitar processamento duplicado.</p></div>}
  <button className="btn-primary mt-5 w-full" disabled={!file||busy} onClick={()=>void send()}>{busy?<><LoaderCircle size={17} className="animate-spin"/> Aguarde o processamento</>:'Transcrever e preparar para análise'}</button>
  <p className="muted mt-3 text-xs">O processamento pode demorar até 10 minutos; a API hospedada pode levar tempo para iniciar.</p>
 </section>;
}
