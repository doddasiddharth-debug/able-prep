/* Accounts and sync. Supabase email + password, one row per user in
   `progress` holding the whole Store state as JSON.

   Sign-in merges what's on this device with what's on the account (see
   Store.merge), then every save is pushed, debounced, and a pull runs on
   each page load so a second device picks up the latest.

   Without config (assets/js/config.js) everything here is a no-op and the
   app stays browser-only. */
window.Auth = (() => {
  "use strict";
  const cfg = window.ABLE_CONFIG || {};
  const enabled = !!(cfg.supabaseUrl && cfg.supabaseAnonKey);
  const SDK = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js";
  let client = null, user = null, ready = null, pushTimer = null, lastPushed = "";
  let status = "idle"; // idle | syncing | synced | offline | error
  let recovery = false; // arrived by a password-reset link
  const listeners = [], pullListeners = [];
  const emit = () => listeners.forEach((fn) => fn(user, status));
  const onChange = (fn) => { listeners.push(fn); };
  const onPull = (fn) => { pullListeners.push(fn); };
  const setStatus = (s) => { status = s; emit(); };

  const loadSdk = () => new Promise((res, rej) => {
    if (window.supabase) return res();
    const s = document.createElement("script");
    s.src = SDK; s.onload = res; s.onerror = () => rej(new Error("Couldn't load the sign-in library."));
    document.head.appendChild(s);
  });

  // ---- sync ---------------------------------------------------------------
  const pull = async () => {
    if (!client || !user) return;
    setStatus("syncing");
    const { data, error } = await client.from("progress").select("state").eq("user_id", user.id).maybeSingle();
    if (error) { setStatus("error"); console.warn("pull", error.message); return; }
    const local = Store.load();
    const remote = data && data.state;
    const merged = remote ? Store.merge(local, remote) : local;
    lastPushed = ""; // force the merged copy up
    Store.replace(merged);
    pullListeners.forEach((fn) => fn());
    await push(true);
  };
  const push = async (now) => {
    if (!client || !user) return;
    clearTimeout(pushTimer);
    const run = async () => {
      const body = JSON.stringify(Store.load());
      if (body === lastPushed) { setStatus("synced"); return; }
      setStatus("syncing");
      const { error } = await client.from("progress").upsert({ user_id: user.id, state: JSON.parse(body), updated_at: new Date().toISOString() });
      if (error) { setStatus(navigator.onLine ? "error" : "offline"); console.warn("push", error.message); return; }
      lastPushed = body; setStatus("synced");
    };
    if (now) return run();
    pushTimer = setTimeout(run, 1500);
  };
  const flush = () => { if (pushTimer) { clearTimeout(pushTimer); push(true); } };

  // ---- session ------------------------------------------------------------
  const init = () => {
    if (!enabled) return Promise.resolve();
    if (ready) return ready;
    ready = loadSdk().then(async () => {
      client = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, { auth: { flowType: "pkce", detectSessionInUrl: true, persistSession: true } });
      const { data } = await client.auth.getSession();
      user = data.session ? data.session.user : null;
      // Password-reset and confirmation links land with ?code=…; once the
      // SDK has exchanged it, tidy the address so the router sees only the hash.
      if (location.search.includes("code=")) history.replaceState(null, "", location.pathname + location.hash);
      client.auth.onAuthStateChange((event, session) => {
        const next = session ? session.user : null;
        const changed = (next && next.id) !== (user && user.id);
        user = next;
        if (event === "PASSWORD_RECOVERY") { recovery = true; location.hash = "#/account"; }
        if (changed) { lastPushed = ""; if (user) pull(); else setStatus("idle"); }
        emit();
      });
      Store.subscribe(() => { if (user) push(); });
      window.addEventListener("beforeunload", flush);
      window.addEventListener("online", () => { if (user) push(true); });
      if (user) await pull();
      emit();
    }).catch((err) => { console.warn(err); setStatus("error"); });
    return ready;
  };

  const redirectTo = () => location.origin + location.pathname + "#/account";
  const signUp = async (email, password) => {
    const { data, error } = await client.auth.signUp({ email, password, options: { emailRedirectTo: redirectTo() } });
    if (error) throw error;
    // With "Confirm email" on, there is a user but no session yet.
    return { needsConfirm: !data.session };
  };
  const signIn = async (email, password) => {
    const { error } = await client.auth.signInWithPassword({ email, password });
    if (error) throw error;
  };
  const signOut = async () => {
    await push(true);
    await client.auth.signOut();
    user = null; lastPushed = ""; setStatus("idle");
    // Shared computers: the next person must not inherit this progress.
    // The account keeps its copy.
    Store.reset();
  };
  const resetPassword = async (email) => {
    const { error } = await client.auth.resetPasswordForEmail(email, { redirectTo: redirectTo() });
    if (error) throw error;
  };
  const updatePassword = async (password) => {
    const { error } = await client.auth.updateUser({ password });
    if (error) throw error;
    recovery = false;
  };
  const deleteData = async () => {
    if (!client || !user) return;
    const { error } = await client.from("progress").delete().eq("user_id", user.id);
    if (error) throw error;
    lastPushed = "";
  };

  return {
    enabled, init, onChange, onPull, pull, push,
    user: () => user, status: () => status, inRecovery: () => recovery,
    signUp, signIn, signOut, resetPassword, updatePassword, deleteData
  };
})();
