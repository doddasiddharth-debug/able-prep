/* Accounts run on Supabase. Paste the project's URL and anon (public) key
   from Project Settings → API. The anon key is safe to ship: row-level
   security on the `progress` table means a user can only ever read and write
   their own row. Leave both blank and the app runs without accounts. */
window.ABLE_CONFIG = {
  supabaseUrl: "https://kwtyihvcwydjwmmrrljg.supabase.co",
  supabaseAnonKey: "sb_publishable_tFCjx9O1uKLqRuy_R1zfEA_FIs3Ti29"
};
