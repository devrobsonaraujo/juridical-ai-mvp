
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error(
    'Supabase não configurado. Verifique as variáveis de ambiente.'
  );
}

const normalizedUrl = supabaseUrl.replace(/\/+$/, '');

if (
  normalizedUrl.includes('/rest/v1') ||
  normalizedUrl.includes('/auth/v1')
) {
  throw new Error(
    'VITE_SUPABASE_URL deve conter somente a URL base do projeto Supabase.'
  );
}

export const supabase = createClient(
  normalizedUrl,
  supabaseKey,
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  }
);
