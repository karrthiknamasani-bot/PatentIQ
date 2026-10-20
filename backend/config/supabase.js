const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.warn('WARNING: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env');
}

// Administrative client to run calculations, indexing, and bypass RLS on server tasks after verifying ownership
const supabaseAdmin = createClient(supabaseUrl || 'https://placeholder.supabase.co', supabaseServiceKey || 'placeholder', {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Default client
const supabase = createClient(supabaseUrl || 'https://placeholder.supabase.co', supabaseAnonKey || supabaseServiceKey || 'placeholder', {
  auth: {
    persistSession: false
  }
});

module.exports = {
  supabase,
  supabaseAdmin
};
