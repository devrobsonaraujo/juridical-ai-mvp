
import { useState, type FormEvent } from 'react';

import {
  Scale,
  Moon,
  Sun,
  ShieldCheck,
  AudioLines,
  MessageSquareText,
  LoaderCircle,
} from 'lucide-react';

import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

export function LoginPage() {
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (submitting) return;

    setError('');
    setSubmitting(true);

    try {
      await login(email, password);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Não foi possível realizar o login.'
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-screen min-h-screen p-4 sm:p-8">
      <div className="mx-auto flex max-w-6xl justify-end">
        <button
          className="icon-button"
          type="button"
          onClick={toggleTheme}
          aria-label={
            theme === 'dark'
              ? 'Ativar modo claro'
              : 'Ativar modo escuro'
          }
        >
          {theme === 'dark' ? (
            <Sun size={20} />
          ) : (
            <Moon size={20} />
          )}
        </button>
      </div>

      <div className="mx-auto grid min-h-[calc(100vh-100px)] max-w-6xl items-center gap-10 lg:grid-cols-2 lg:gap-20">
        <section className="hidden lg:block">
          <span className="eyebrow">
            LEGALTECH • INTELIGÊNCIA PROBATÓRIA
          </span>

          <h1 className="mt-4 max-w-xl text-5xl font-bold leading-tight tracking-tight">
            Mais clareza nas audiências.{' '}
            <span className="text-[var(--accent)]">
              Menos tempo procurando respostas.
            </span>
          </h1>

          <p className="muted mt-6 max-w-lg !text-base">
            Transcreva gravações, consulte informações e
            encontre os trechos relevantes com apoio de
            inteligência artificial.
          </p>

          <div className="mt-10 grid max-w-lg gap-4">
            <div className="flex items-center gap-3">
              <AudioLines className="text-[var(--accent)]" />
              Transcrição de áudio e vídeo
            </div>

            <div className="flex items-center gap-3">
              <MessageSquareText
                className="text-[var(--accent)]"
              />
              Perguntas sobre a audiência
            </div>

            <div className="flex items-center gap-3">
              <ShieldCheck
                className="text-[var(--accent)]"
              />
              Respostas acompanhadas de fontes
            </div>
          </div>
        </section>

        <form
          onSubmit={(event) => void submit(event)}
          className="panel mx-auto w-full max-w-md !p-7 sm:!p-9"
        >
          <span className="brand-icon mb-6 inline-flex rounded-2xl p-4">
            <Scale size={29} />
          </span>

          <h2 className="text-2xl font-bold tracking-tight">
            Bem-vindo ao Juridical AI
          </h2>

          <p className="muted mb-8 mt-2">
            Entre para acessar suas ferramentas de análise.
          </p>

          <label className="label" htmlFor="email">
            E-mail
          </label>

          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            disabled={submitting}
            className="field mb-5"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              setError('');
            }}
            placeholder="advogado@exemplo.com"
          />

          <div className="mb-2 flex items-center justify-between gap-3">
            <label className="label" htmlFor="password">
              Senha
            </label>

            <a
              href="/forgot-password"
              className="text-xs font-medium text-[var(--accent)] hover:underline"
            >
              Esqueceu sua senha?
            </a>
          </div>

          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            disabled={submitting}
            className="field mb-5"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setError('');
            }}
            placeholder="Sua senha"
          />

          {error && (
            <p
              role="alert"
              className="mb-4 text-sm text-red-500"
            >
              {error}
            </p>
          )}

          <button
            className="btn-primary flex w-full items-center justify-center gap-2"
            type="submit"
            disabled={submitting}
          >
            {submitting ? (
              <>
                <LoaderCircle
                  size={18}
                  className="animate-spin"
                />
                Entrando...
              </>
            ) : (
              'Entrar na plataforma'
            )}
          </button>

          <p className="muted mt-6 text-center text-xs">
            Acesso exclusivo para usuários autorizados.
          </p>

          <p className="mt-3 text-center text-xs text-amber-600">
            Versão de testes. Não utilize dados jurídicos
            confidenciais nesta etapa.
          </p>
        </form>
      </div>
    </main>
  );
}
