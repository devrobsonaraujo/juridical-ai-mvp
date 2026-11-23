import { AudioLines, MessageSquareText, LogOut, Scale, Server, X, Moon, Sun } from 'lucide-react';
import { API_BASE_URL } from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
export type Page = 'transcription' | 'rag';
export function Sidebar({ page, setPage, open, close }: { page: Page; setPage: (p: Page) => void; open: boolean; close: () => void }) {
 const { user, logout } = useAuth(); const { theme, toggleTheme } = useTheme();
 return <><div aria-hidden="true" onClick={close} className={`fixed inset-0 z-30 bg-black/60 lg:hidden ${open ? '' : 'hidden'}`}/><aside aria-label="Navegação principal" className={`app-sidebar fixed inset-y-0 left-0 z-40 flex w-[min(19rem,86vw)] flex-col border-r p-5 transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:w-72 lg:shrink-0 lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
 <div className="mb-10 flex items-center gap-3"><span className="brand-icon rounded-2xl p-3"><Scale size={24}/></span><div className="min-w-0"><strong className="block text-lg tracking-tight">Juridical AI</strong><p className="muted !text-xs">Inteligência probatória</p></div><button aria-label="Fechar menu" onClick={close} className="icon-button ml-auto lg:hidden"><X size={20}/></button></div>
 <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[.16em] text-[var(--muted)]">Workspace</p>
 {([{ id: 'transcription', label: 'Audiências', Icon: AudioLines }, { id: 'rag', label: 'Assistente jurídico', Icon: MessageSquareText }] as const).map(({ id, label, Icon }) => <button key={id} type="button" aria-current={page === id ? 'page' : undefined} onClick={() => { setPage(id); close(); }} className={`nav-item mb-2 flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-semibold ${page === id ? 'nav-active' : ''}`}><Icon size={19}/>{label}</button>)}
 <div className="mt-auto space-y-4 pt-6"><div className="soft-card rounded-xl p-3 text-xs"><div className="mb-2 flex items-center gap-2 font-semibold"><Server size={15}/> API configurada</div><p className="break-all text-[var(--muted)]">{API_BASE_URL}</p><p className="mt-2 text-[var(--muted)]">A URL não garante conectividade.</p></div><button type="button" onClick={toggleTheme} className="nav-item flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm lg:hidden">{theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>} {theme === 'dark' ? 'Modo claro' : 'Modo escuro'}</button><p className="truncate px-2 text-xs text-[var(--muted)]" title={user || ''}>{user}</p><button onClick={logout} className="nav-item flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-500"><LogOut size={17}/> Sair do sistema</button></div>
 </aside></>;
}
