/* Accounts run on Supabase. Paste the project's URL and anon (public) key
   from Project Settings → API. The anon key is safe to ship: row-level
   security on the `progress` table means a user can only ever read and write
   their own row. Leave both blank and the app runs without accounts. */
window.ABLE_CONFIG = {
  supabaseUrl: "",
  supabaseAnonKey: ""
};
