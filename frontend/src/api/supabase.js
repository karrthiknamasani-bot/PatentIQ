import { createClient } from '@supabase/supabase-js';

const rawUrl = import.meta.env.VITE_SUPABASE_URL;
const rawKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(
  rawUrl &&
  rawKey &&
  !rawUrl.includes('placeholder') &&
  !rawUrl.includes('your-project')
);

// Only instantiate real client when valid configuration is provided
export const supabase = isSupabaseConfigured
  ? createClient(rawUrl, rawKey)
  : null;
