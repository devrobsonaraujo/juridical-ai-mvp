import { useState, type ReactNode } from 'react';
import { Menu, Moon, Sun } from 'lucide-react';
import { Sidebar, type Page } from './Sidebar';
import { useTheme } from '../../contexts/ThemeContext';
export function AppLayout({ page, setPage, children }: { page: Page; setPage: (p: Page) => void; children: ReactNode }) {
 const [open, setOpen] = useState(false);
 const { theme, toggleTheme } = useTheme();
 return <div className="app-shell min-h-screen lg:flex"><Sidebar page={page} setPage={setPage} open={open} close={() => setOpen(false)}/><div className="min-w-0 flex-1"><header className="app-topbar sticky top-0 z-20 flex h-16 items-center justify-between border-b px-4 sm:px-6 lg:px-10"><div className="flex items-center gap-3"><button type="button" aria-label="Abrir menu" className="icon-button lg:hidden" onClick={() => setOpen(true)}><Menu size={21}/></button><span className="text-sm font-semibold lg:hidden">Juridical AI</span><span className="hidden text-sm font-medium lg:inline">Workspace / {page === 'transcription' ? 'Audiências' : 'Assistente jurídico'}</span></div><button type="button" onClick={toggleTheme} className="icon-button" aria-label={theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'} title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}>{theme === 'dark' ? <Sun size={19}/> : <Moon size={19}/>}</button></header><main id="main-content" className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10">{children}</main></div></div>;
}
