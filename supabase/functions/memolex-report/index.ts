// Memolex — transmet un signalement de carte (table memolex_report) vers une issue GitHub.
// Appelée par le trigger memolex_report_notify (en-tête x-report-secret, corps {"id": n}).
// Secrets (Supabase → Edge Functions → Secrets) : REPORT_SECRET, GITHUB_TOKEN (jeton « fine-grained », droit Issues : lecture et écriture
// sur le seul dépôt des signalements), GITHUB_REPO (facultatif, par défaut memolex-app/signalements).
// « Verify JWT » doit être désactivé : la fonction vérifie elle-même l'en-tête secret.
import { createClient } from "npm:@supabase/supabase-js@2";

const REASON: Record<string, string> = { trad: "Traduction incorrecte", exemple: "Phrase d'exemple douteuse", chunk: "Expression « À retenir » fausse", gram: "Article, pluriel, nature ou cas faux", offensif: "Contenu choquant ou offensant", autre: "Autre" };
const LANG: Record<string, string> = { de: "allemand", it: "italien" };
const clip = (s: unknown, n: number) => String(s ?? "").replace(/\s+/g, " ").slice(0, n);

export function issueOf(r: any) {
  const c = r.card || {};
  const word = (c.art ? c.art + (/'$/.test(c.art) ? "" : " ") : "") + (c.de || "?");
  const title = clip(`[${r.lang}] ${word} — ${REASON[r.reason] || r.reason}`, 200);
  const L: string[] = [];
  L.push(`**Motif** : ${REASON[r.reason] || r.reason}`);
  if (r.comment) L.push(`**Commentaire de l'utilisateur** :\n> ${clip(r.comment, 1000)}`);
  L.push("", "### Carte telle qu'elle était affichée");
  L.push(`- Langue : ${LANG[r.lang] || r.lang} → français · niveau ${c.lvl || "?"} · nature ${c.pos || "?"}`);
  L.push(`- Mot : \`${word}\`${c.pl ? ` · pluriel \`${c.pl}\`` : ""}`);
  L.push(`- Traduction : \`${clip(c.fr, 300)}\`${c.frOwn ? " (modifiée par l'utilisateur)" : ""}`);
  L.push(`- Origine : ${c.src === "lists" ? "listes Memolex" : "mot ajouté par l'utilisateur"} · clé \`${clip(c.key, 120)}\` · sens de révision ${c.dir || "?"}`);
  if (c.chunk) L.push(`- À retenir : ${clip(c.chunk[0], 200)} — ${clip(c.chunk[1], 200)}`);
  if (c.def) L.push(`- Définition : ${clip(c.def, 400)}`);
  if (c.ownEx) L.push(`- Exemple de l'utilisateur : ${clip(c.ownEx, 300)}`);
  for (const e of c.ex || []) L.push(`- Exemple${e[2] ? ` (${clip(e[2], 60)})` : ""} : ${clip(e[0], 300)} — ${clip(e[1], 300)}`);
  L.push("", `<sub>Signalement n° ${r.id} · ${r.created_at} · appli ${r.app_ver || "?"} · ${r.user_id ? "utilisateur connecté" : "anonyme"}</sub>`);
  return { title, body: L.join("\n"), labels: ["nouveau", r.reason, r.lang] };
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("POST", { status: 405 });
  const secret = Deno.env.get("REPORT_SECRET");
  if (!secret || req.headers.get("x-report-secret") !== secret) return new Response("interdit", { status: 403 });
  const token = Deno.env.get("GITHUB_TOKEN"), repo = Deno.env.get("GITHUB_REPO") || "memolex-app/signalements";
  if (!token) return new Response("secret GITHUB_TOKEN manquant", { status: 500 });
  let id: number; try { id = Number((await req.json()).id); } catch (_) { return new Response("corps invalide", { status: 400 }); }
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { data: r, error } = await db.from("memolex_report").select("*").eq("id", id).single();
  if (error || !r) return new Response("signalement introuvable", { status: 404 });
  if (r.gh_issue) return Response.json({ issue: r.gh_issue, already: true });
  const res = await fetch(`https://api.github.com/repos/${repo}/issues`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "memolex-report" },
    body: JSON.stringify(issueOf(r)),
  });
  if (!res.ok) return new Response(`GitHub ${res.status} : ${(await res.text()).slice(0, 300)}`, { status: 502 });
  const issue = await res.json();
  await db.from("memolex_report").update({ gh_issue: issue.number }).eq("id", id);
  return Response.json({ issue: issue.number });
});
