
import { useState } from 'react';
import { LoaderCircle, Scale } from 'lucide-react';

import { AppLayout } from './components/layout/AppLayout';
import type { Page } from './components/layout/Sidebar';

import { useAuth } from './contexts/AuthContext';

import { LoginPage } from './pages/LoginPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';

import { TranscriptionPage } from './pages/TranscriptionPage';
import { RagPage } from './pages/RagPage';

export default function App() {
  const { user, loading } = useAuth();

  const [page, setPage] = useState<Page>('transcription');
  const [selectedMedia, setSelectedMedia] = useState('');

  const pathname = window.location.pathname;

  function consultMedia(filename: string) {
    setSelectedMedia(filename);
    setPage('rag');
  }

  // Páginas públicas de recuperação de senha.
  if (pathname === '/forgot-password') {
    return <ForgotPasswordPage />;
  }

  if (pathname === '/reset-password') {
    return <ResetPasswordPage />;
  }

  if (loading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4">
        <Scale
          size={36}
          className="text-[var(--accent)]"
        />

        <LoaderCircle
          size={24}
          className="animate-spin text-[var(--accent)]"
        />

        <p className="muted text-sm">
          Verificando sua sessão...
        </p>
      </main>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <AppLayout page={page} setPage={setPage}>
      <div hidden={page !== 'transcription'}>
        <TranscriptionPage onConsult={consultMedia} />
      </div>

      <div hidden={page !== 'rag'}>
        <RagPage
          selectedMedia={selectedMedia}
          onSelectMedia={setSelectedMedia}
        />
      </div>
    </AppLayout>
  );
}
