// Memolex — envoi des rappels et du mot du jour (Web Push).
// Appelée toutes les 15 min par pg_cron (en-tête x-cron-secret), ou par l'appli pour un test (jeton de l'utilisateur, corps {"test":true}).
// Secrets à définir dans Supabase → Edge Functions → Secrets : VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, CRON_SECRET.
// « Verify JWT » doit être désactivé pour cette fonction : elle vérifie elle-même qui l'appelle.
import { createClient } from "npm:@supabase/supabase-js@2";
import webpush from "npm:web-push@3.6.7";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-cron-secret", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const WINDOW = 30; // minutes : un créneau est servi par le premier passage du cron dans les 30 min qui suivent son heure

// ---------- logique pure (testée hors Supabase) ----------
export function localNow(tz, now) {
  let p;
  try { p = new Intl.DateTimeFormat("en-CA", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(now); }
  catch (_) { p = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(now); }
  const g = (t) => (p.find((x) => x.type === t) || {}).value;
  return { date: `${g("year")}-${g("month")}-${g("day")}`, min: (+g("hour")) * 60 + (+g("minute")) };
}
const toMin = (t) => { const [h, m] = String(t).split(":").map(Number); return h * 60 + (m || 0); };
const inWin = (nowMin, t) => { const d = nowMin - toMin(t); return d >= 0 && d < WINDOW; };
export const wordLine = (f) => (f.art ? f.art + (/'$/.test(f.art) ? "" : " ") : "") + f.de;

// ce qu'il faut envoyer maintenant à un utilisateur : [{key, kind, ...}]
export function plan(s, now, sent) {
  s = s || {};
  const n = { on: false, times: ["08:00", "19:30"], wotd: true, wotdAt: "10:00", ...(s.notif || {}) };
  if (!n.on) return [];
  const { date, min } = localNow(s.tz || "Europe/Paris", now);
  const out = [];
  const dayMin = s.dayMin || 10;
  let done = 0; for (const L in (s.act || {})) done += ((s.act[L] || {})[date] || {}).n || 0;
  for (const t of n.times || []) {
    const key = date + ":" + t;
    if (inWin(min, t) && !sent[key] && done < dayMin) { out.push({ key, kind: "rem", done, dayMin, slot: t }); break; }
  }
  if (n.wotd !== false && inWin(min, n.wotdAt || "10:00") && !sent[date + ":w"]) {
    const f = s.wotd && s.wotd.days && s.wotd.days[date];
    if (f) out.push({ key: date + ":w", kind: "wotd", f, lang: s.wotd.lang || "de" });
  }
  return out;
}
// textes des notifications, dans la langue de l'utilisateur (settings.wotd.ul, français par défaut)
const pl = (n, one, other) => (n > 1 ? other : one);
const TXT = {
  fr: {
    wotd: "Mot du jour",
    due: (n, m) => `${n} ${pl(n, "mot", "mots")} à revoir, environ ${m} min.`,
    fresh: (m) => `Quelques nouveaux mots, environ ${m} min ?`,
    left: (n) => ` Encore ${n} ${pl(n, "carte", "cartes")} pour compter la journée.`,
    morning: "Bonjour ! C'est l'heure de tes mots", midday: "Une pause vocabulaire ?", evening: "Tes mots du jour t'attendent",
    test: "Les notifications fonctionnent sur cet appareil.",
  },
  en: {
    wotd: "Word of the day",
    due: (n, m) => `${n} ${n === 1 ? "word" : "words"} to review, about ${m} min.`,
    fresh: (m) => `A few new words, about ${m} min?`,
    left: (n) => ` ${n} more ${n === 1 ? "card" : "cards"} to make today count.`,
    morning: "Good morning! Time for your words", midday: "A vocabulary break?", evening: "Your words for today are waiting",
    test: "Notifications work on this device.",
  },
};
export const txt = (ul) => TXT[ul] || TXT.fr;
export function message(item, due, ul = "fr") {
  const t = txt(ul);
  if (item.kind === "wotd") return { kind: "wotd", ul, title: `${t.wotd} · ${item.f.lvl || ""}`.trim().replace(/ ·$/, ""), body: `${wordLine(item.f)} — ${item.f.fr}`, word: { f: item.f, lang: item.lang } };
  const left = item.dayMin - item.done;
  const mins = Math.max(1, Math.round(Math.max(due, left) * 10 / 60));
  const head = due > 0 ? t.due(due, mins) : t.fresh(mins);
  const tail = item.done > 0 ? t.left(left) : "";
  const title = item.slot < "11:00" ? t.morning : item.slot < "16:00" ? t.midday : t.evening;
  return { kind: "rem", ul, title, body: head + tail };
}
// mots déjà vus et dus maintenant, dans la langue apprise
export function countDue(rows, lang, nowMs) {
  let n = 0;
  for (const r of rows) { const d = r.data || {}; if ((d.lang || "de") !== lang) continue;
    const isNew = (d.reps || 0) === 0 && (d.lapses || 0) === 0 && d.ls == null;
    if (!isNew && (d.due || 0) <= nowMs) n++; }
  return n;
}
const prune = (sent, now) => { const lim = new Date(now.getTime() - 3 * 86400000).toISOString().slice(0, 10); const o = {}; for (const k in sent) if (k.slice(0, 10) >= lim) o[k] = sent[k]; return o; };

// ---------- serveur ----------
if (typeof Deno !== "undefined") Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const json = (o, st = 200) => new Response(JSON.stringify(o), { status: st, headers: { ...CORS, "Content-Type": "application/json" } });
  const url = Deno.env.get("SUPABASE_URL"), key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const pub = Deno.env.get("VAPID_PUBLIC_KEY"), priv = Deno.env.get("VAPID_PRIVATE_KEY"), secret = Deno.env.get("CRON_SECRET");
  if (!url || !key || !pub || !priv) return json({ error: "secrets manquants" }, 500);
  webpush.setVapidDetails("mailto:frankcarnation@gmail.com", pub, priv);
  const db = createClient(url, key, { auth: { persistSession: false } });
  let body = {}; try { body = await req.json(); } catch (_) {}
  const now = new Date();

  // qui appelle ?
  let testUser = null;
  if (body.test) {
    const tok = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
    const { data, error } = await db.auth.getUser(tok);
    if (error || !data || !data.user) return json({ error: "non connecté" }, 401);
    testUser = data.user.id;
  } else if (!secret || req.headers.get("x-cron-secret") !== secret) return json({ error: "interdit" }, 403);

  let q = db.from("memolex_push").select("endpoint,user_id,sub,sent");
  if (testUser) q = q.eq("user_id", testUser);
  const { data: subs, error: e1 } = await q;
  if (e1) return json({ error: e1.message }, 500);
  if (!subs || !subs.length) return json({ sent: 0 });
  const users = [...new Set(subs.map((s) => s.user_id))];
  const { data: sets } = await db.from("memolex").select("user_id,data").eq("id", "_settings").in("user_id", users);
  const S = new Map((sets || []).map((r) => [r.user_id, r.data || {}]));

  const send = async (s, msg) => {
    try { await webpush.sendNotification(s.sub, JSON.stringify(msg), { TTL: 3600 }); return true; }
    catch (err) { if (err && (err.statusCode === 404 || err.statusCode === 410)) await db.from("memolex_push").delete().eq("endpoint", s.endpoint); return false; }
  };
  let sent = 0;
  const dueCache = new Map();
  for (const s of subs) {
    const st = S.get(s.user_id) || {};
    const ul = (st.wotd && st.wotd.ul) || "fr";
    if (testUser) {
      if (await send(s, { kind: "test", ul, title: "Memolex", body: txt(ul).test })) sent++;
      const f = st.wotd && st.wotd.days && st.wotd.days[localNow(st.tz || "Europe/Paris", now).date];
      if (f) await send(s, message({ kind: "wotd", f, lang: st.wotd.lang || "de" }, 0, ul));
      continue;
    }
    const todo = plan(st, now, s.sent || {});
    if (!todo.length) continue;
    const mark = { ...(s.sent || {}) };
    for (const it of todo) {
      let due = 0;
      if (it.kind === "rem") {
        const lang = (st.wotd && st.wotd.lang) || "de";
        if (!dueCache.has(s.user_id)) {
          const { data: rows } = await db.from("memolex").select("data").eq("user_id", s.user_id).eq("deleted", false).neq("id", "_settings").limit(20000);
          dueCache.set(s.user_id, countDue(rows || [], lang, now.getTime()));
        }
        due = dueCache.get(s.user_id);
      }
      if (await send(s, message(it, due, ul))) sent++;
      mark[it.key] = now.toISOString();
    }
    await db.from("memolex_push").update({ sent: prune(mark, now) }).eq("endpoint", s.endpoint);
  }
  return json({ sent });
});
