
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import type { User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

type AccessStatus = 'pending' | 'active' | 'suspended';

type Auth = {
  user: string | null;
  authUser: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const Context = createContext<Auth | null>(null);

function isRecoveryRoute(): boolean {
  return window.location.pathname === '/reset-password';
}

function accessError(status: AccessStatus): Error {
  if (status === 'suspended') {
    return new Error(
      'Sua conta está suspensa. Entre em contato com o suporte.'
    );
  }

  return new Error(
    'Seu acesso ainda não foi liberado. ' +
    'Entre em contato com o administrador.'
  );
}

async function validateAccess(userId: string): Promise<void> {
  const { data, error } = await supabase
    .from('profiles')
    .select('access_status')
    .eq('id', userId)
    .single();

  if (error || !data) {
    throw new Error(
      'Não foi possível validar sua permissão de acesso.'
    );
  }

  const status = data.access_status as AccessStatus;

  if (status !== 'active') {
    throw accessError(status);
  }
}

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] = useState<string | null>(null);
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const validationId = useRef(0);

  const clearUser = useCallback(() => {
    setUser(null);
    setAuthUser(null);
  }, []);

  const checkSession = useCallback(
    async (currentUser: User | null) => {
      const currentValidation = ++validationId.current;

      if (isRecoveryRoute()) {
        clearUser();
        setLoading(false);
        return;
      }

      if (!currentUser) {
        clearUser();
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        await validateAccess(currentUser.id);

        if (currentValidation !== validationId.current) {
          return;
        }

        setAuthUser(currentUser);
        setUser(currentUser.email ?? currentUser.id);
      } catch {
        if (currentValidation !== validationId.current) {
          return;
        }

        clearUser();
      } finally {
        if (currentValidation === validationId.current) {
          setLoading(false);
        }
      }
    },
    [clearUser]
  );

  useEffect(() => {
    let mounted = true;

    async function initialize() {
      try {
        const { data } = await supabase.auth.getSession();

        if (mounted) {
          await checkSession(data.session?.user ?? null);
        }
      } catch {
        if (mounted) {
          clearUser();
          setLoading(false);
        }
      }
    }

    void initialize();

    const { data: listener } =
      supabase.auth.onAuthStateChange((event, session) => {
        if (!mounted) return;

        if (event === 'PASSWORD_RECOVERY') {
          clearUser();
          setLoading(false);
          return;
        }

        if (
          event === 'SIGNED_IN' ||
          event === 'SIGNED_OUT' ||
          event === 'USER_UPDATED'
        ) {
          void checkSession(session?.user ?? null);
        }
      });

    return () => {
      mounted = false;
      validationId.current += 1;
      listener.subscription.unsubscribe();
    };
  }, [checkSession, clearUser]);

  const login = async (
    email: string,
    password: string
  ): Promise<void> => {
    const normalizedEmail = email.trim().toLowerCase();

    if (!normalizedEmail || !password) {
      throw new Error('Informe seu e-mail e sua senha.');
    }

    const { data, error } =
      await supabase.auth.signInWithPassword({
        email: normalizedEmail,
        password,
      });

    if (error || !data.user) {
      throw new Error(
        'E-mail ou senha inválidos. Verifique suas credenciais.'
      );
    }

    try {
      await validateAccess(data.user.id);
      await checkSession(data.user);
    } catch (error) {
      await supabase.auth.signOut();
      clearUser();
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    const { error } = await supabase.auth.signOut();

    if (error) {
      throw new Error(
        'Não foi possível encerrar sua sessão. Tente novamente.'
      );
    }

    validationId.current += 1;
    clearUser();
    setLoading(false);
  };

  return (
    <Context.Provider
      value={{
        user,
        authUser,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </Context.Provider>
  );
}

export function useAuth(): Auth {
  const context = useContext(Context);

  if (!context) {
    throw new Error(
      'useAuth deve ser utilizado dentro de AuthProvider.'
    );
  }

  return context;
}
