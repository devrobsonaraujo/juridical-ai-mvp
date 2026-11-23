
import {
  useEffect,
  useState,
  type FormEvent,
} from 'react';

import {
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  Scale,
} from 'lucide-react';

import { supabase } from '../lib/supabase';

type RecoveryState =
  | 'checking'
  | 'ready'
  | 'invalid'
  | 'success';

export function ResetPasswordPage() {
  const [state, setState] =
    useState<RecoveryState>('checking');

  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    let recoveryConfirmed = false;

    const hashParams = new URLSearchParams(
      window.location.hash.replace(/^#/, '')
    );

    const queryParams = new URLSearchParams(
      window.location.search
    );

    const linkError =
      hashParams.has('error') ||
      queryParams.has('error');

    if (linkError) {
      setState('invalid');
      return;
    }

    const { data: listener } =
      supabase.auth.onAuthStateChange(
        (event, session) => {
          if (!mounted) return;

          if (
            event === 'PASSWORD_RECOVERY' &&
            session
          ) {
            recoveryConfirmed = true;
            setState('ready');
          }

          if (
            event === 'SIGNED_OUT' &&
            !recoveryConfirmed
          ) {
            setState('invalid');
          }
        }
      );

    async function checkRecovery() {
      const { data, error: sessionError } =
        await supabase.auth.getSession();

      if (!mounted || recoveryConfirmed) return;

      if (sessionError || !data.session) {
        setState('invalid');
        return;
      }

      // O Supabase pode recuperar a sessão antes de
      // emitir PASSWORD_RECOVERY. Aguardamos brevemente
      // para evitar classificar o link como inválido.
      window.setTimeout(() => {
        if (mounted && !recoveryConfirmed) {
          setState('invalid');
        }
      }, 1500);
    }

    void checkRecovery();

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (loading || state !== 'ready') return;

    setError('');

    if (password.length < 12) {
      setError(
        'A senha deve conter pelo menos 12 caracteres.'
      );
      return;
    }

    if (password !== confirmation) {
      setError('As senhas informadas não coincidem.');
      return;
    }

    setLoading(true);

    try {
      const { error: updateError } =
        await supabase.auth.updateUser({
          password,
        });

      if (updateError) {
        throw updateError;
      }

      setState('success');
      setPassword('');
      setConfirmation('');

      const { error: signOutError } =
        await supabase.auth.signOut();

      if (signOutError) {
        setError(
          'Senha alterada, mas não foi possível ' +
          'encerrar a sessão automaticamente.'
        );
      }
    } catch {
      setError(
        'Não foi possível atualizar sua senha. ' +
        'Solicite um novo link e tente novamente.'
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

        {state === 'checking' && (
          <div
            className="flex flex-col items-center gap-4 py-8"
            role="status"
          >
            <LoaderCircle
              size={30}
              className="animate-spin text-[var(--accent)]"
            />

            <p className="muted text-sm">
              Validando seu link de recuperação...
            </p>
          </div>
        )}

        {state === 'invalid' && (
          <>
            <KeyRound
              size={34}
              className="mb-4 text-amber-500"
            />

            <h1 className="text-2xl font-bold">
              Link inválido ou expirado
            </h1>

            <p className="muted mt-3 text-sm leading-6">
              Não foi possível validar este link.
              Ele pode ter expirado ou já ter sido utilizado.
              Solicite uma nova recuperação de senha.
            </p>

            <a
              href="/forgot-password"
              className="btn-primary mt-8 flex w-full items-center justify-center"
            >
              Solicitar novo link
            </a>
          </>
        )}

        {state === 'success' && (
          <>
            <CheckCircle2
              size={36}
              className="mb-4 text-emerald-500"
            />

            <h1 className="text-2xl font-bold">
              Senha atualizada!
            </h1>

            <p className="muted mt-3 text-sm leading-6">
              Sua senha foi alterada com sucesso.
              Agora você pode entrar no Juridical AI
              utilizando suas novas credenciais.
            </p>

            {error && (
              <p
                role="alert"
                className="mt-4 text-sm text-amber-600"
              >
                {error}
              </p>
            )}

            <a
              href="/"
              className="btn-primary mt-8 flex w-full items-center justify-center"
            >
              Ir para o login
            </a>
          </>
        )}

        {state === 'ready' && (
          <>
            <div className="mb-4 flex items-center gap-2">
              <KeyRound
                size={20}
                className="text-[var(--accent)]"
              />
              <span className="eyebrow">
                SEGURANÇA DA CONTA
              </span>
            </div>

            <h1 className="text-2xl font-bold">
              Criar nova senha
            </h1>

            <p className="muted mb-8 mt-3 text-sm">
              Escolha uma senha forte para proteger
              seu acesso ao Juridical AI.
            </p>

            <form
              onSubmit={(event) => void handleSubmit(event)}
            >
              <label
                className="label"
                htmlFor="new-password"
              >
                Nova senha
              </label>

              <div className="relative mb-5">
                <input
                  id="new-password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  minLength={12}
                  disabled={loading}
                  className="field w-full pr-12"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setError('');
                  }}
                  placeholder="Mínimo de 12 caracteres"
                />

                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? 'Ocultar senha'
                      : 'Mostrar senha'
                  }
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>

              <label
                className="label"
                htmlFor="confirm-password"
              >
                Confirmar nova senha
              </label>

              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                disabled={loading}
                className="field mb-5"
                value={confirmation}
                onChange={(event) => {
                  setConfirmation(event.target.value);
                  setError('');
                }}
                placeholder="Repita sua nova senha"
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
                    Salvando...
                  </>
                ) : (
                  'Atualizar senha'
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
