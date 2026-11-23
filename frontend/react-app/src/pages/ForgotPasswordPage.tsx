
import { useState, type FormEvent } from 'react';
import {
  ArrowLeft,
  CheckCircle2,
  LoaderCircle,
  Mail,
  Scale,
} from 'lucide-react';

import { supabase } from '../lib/supabase';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (loading) return;

    setLoading(true);
    setError('');

    try {
      const { error: recoveryError } =
        await supabase.auth.resetPasswordForEmail(
          email.trim().toLowerCase(),
          {
            redirectTo: `${window.location.origin}/reset-password`,
          }
        );

      if (recoveryError) {
        throw recoveryError;
      }

      setSent(true);
    } catch {
      setError(
        'Não foi possível processar sua solicitação. ' +
        'Aguarde alguns minutos e tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen flex min-h-screen items-center justify-center p-4 sm:p-8">
      <div className="panel w-full max-w-md !p-7 sm:!p-9">
        <span className="brand-icon mb-6 inline-flex rounded-2xl p-4">
          <Scale size={29} />
        </span>

        {sent ? (
          <div aria-live="polite">
            <CheckCircle2
              size={36}
              className="mb-4 text-emerald-500"
            />

            <h1 className="text-2xl font-bold tracking-tight">
              Verifique seu e-mail
            </h1>

            <p className="muted mt-3 text-sm leading-6">
              Se existir uma conta associada ao e-mail
              informado, você receberá instruções para
              redefinir sua senha.
            </p>

            <p className="muted mt-3 text-sm">
              Verifique também sua pasta de spam.
              O link possui prazo de validade.
            </p>

            <a
              href="/"
              className="btn-primary mt-8 flex w-full items-center justify-center"
            >
              Voltar ao login
            </a>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center gap-2">
              <Mail
                size={20}
                className="text-[var(--accent)]"
              />
              <span className="eyebrow">
                RECUPERAÇÃO DE ACESSO
              </span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight">
              Esqueceu sua senha?
            </h1>

            <p className="muted mb-8 mt-3 text-sm leading-6">
              Informe seu e-mail cadastrado no Juridical AI
              para receber um link de recuperação.
            </p>

            <form
              onSubmit={(event) => void handleSubmit(event)}
            >
              <label className="label" htmlFor="recovery-email">
                E-mail
              </label>

              <input
                id="recovery-email"
                type="email"
                autoComplete="email"
                required
                disabled={loading}
                className="field mb-5"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError('');
                }}
                placeholder="advogado@exemplo.com"
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
                type="submit"
                disabled={loading}
                className="btn-primary flex w-full items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <LoaderCircle
                      size={18}
                      className="animate-spin"
                    />
                    Enviando...
                  </>
                ) : (
                  'Enviar link de recuperação'
                )}
              </button>
            </form>

            <a
              href="/"
              className="muted mt-6 flex items-center justify-center gap-2 text-sm hover:underline"
            >
              <ArrowLeft size={16} />
              Voltar ao login
            </a>
          </>
        )}
      </div>
    </main>
  );
}
