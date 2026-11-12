"""Test de non-régression de l'appli, par langue apprise : capture le comportement grammatical et le rendu des écrans.

Usage :
  python3 tools/regress_app.py capture /chemin/sortie.json     enregistre le comportement actuel (référence)
  python3 tools/regress_app.py compare /chemin/reference.json  recapture et compare ; code 1 si une différence

Horloge et hasard figés (Date.now, Math.random) pour un résultat reproductible. Sert le dépôt sur un port local.
Contenu capturé, pour chaque langue (de, it) :
  - pour chaque mot des listes : couleur (gcls), mot affiché (deWord, artWord), ligne de grammaire, cas, cible du quiz
    des cas, boutons du quiz de l'article ;
  - analyse d'un mot tapé (splitArt) et d'une ligne collée (parseLine) sur des cas types ;
  - verdicts du quiz des cas ; article et couleur des entrées du dictionnaire (entArt, entCls, artVal) ;
  - recto et verso d'un échantillon de cartes, dans les deux sens, avant et après réponse ;
  - écrans Mots, Ajouter, Guide, choix de la langue, recherche dans le dictionnaire.
"""
import asyncio, functools, http.server, json, os, sys, threading
from playwright.async_api import async_playwright

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PORT = 8799

INIT = """
(()=>{ let t=1767225600000; Date.now=()=>t; const D=Date; window.Date=class extends D{ constructor(...a){ super(...(a.length?a:[t])); } static now(){ return t; } };
  let s=42; Math.random=()=>{ s=(s*1103515245+12345)%2147483648; return s/2147483648; };
  try{ localStorage.clear(); localStorage.setItem('mx-lang', '%LANG%'); }catch(e){} })();
"""

PROBE = r"""
async (lang) => {
  const wait = async (f, ms=20000) => { const t0=performance.now(); while(!f()){ if(performance.now()-t0>ms) throw new Error('délai'); await new Promise(r=>setTimeout(r,50)); } };
  loadLists(); await wait(()=>listState==='ready');
  loadDict(); await wait(()=>dictState==='ready' || dictState==='error');
  const out = {};
  const words = []; Object.entries(LISTDATA).forEach(([L,a])=>a.forEach(f=>words.push({...f, lang, lvl:L})));
  out.words = words.map(c=>[c.de, c.art, gcls(c), artWord(c), deWord(c), gramLine(c), prepCase(c.de,c), JSON.stringify(caseTarget(c)), c.art?artButtons(c):'']);
  const SPLIT = lang==='de'
    ? ['der Hund','Die Katze','das Haus','den Hund','Hund','der','der  Hund',' das Kind ','dieHund']
    : ['il cane','Lo zio',"l'amico","l’amica","l' anno",'la casa','i cani','gli zii','le case','cane','il','lo'];
  out.split = SPLIT.map(s=>[s, JSON.stringify(splitArt(s))]);
  const LINES = lang==='de'
    ? ['der Hund, -e ; le chien','die Rechnung, -en ; la facture ; Die Rechnung bitte.','bestellen ; commander','das Mittel, - ; le moyen','Hund ; chien','der Hund','; vide']
    : ['il cane, i cani ; le chien',"l'amico, gli amici ; l'ami",'la città, le città ; la ville','ordinare ; commander','i soldi ; l\'argent','le forbici ; les ciseaux','cane ; chien'];
  out.lines = LINES.map(l=>[l, JSON.stringify(parseLine(l))]);
  const preps = words.filter(c=>caseTarget(c));
  out.caseVerdicts = preps.flatMap(c=>['K:Akk','K:Dat','K:Gen','K:Dat+Akk','K:Akk+Dat','K:Gen+Dat'].map(g=>[c.de,g,caseVerdict(c,g),guessWrong(c,g)]));
  out.dict = (DICT||[]).slice(0,3000).map(e=>[e.w, entArt(e), entCls(e)]);
  out.artVal = [['der',''],['die',''],['il',''],['la',''],["l'",'m'],["l'",'f'],["l'",''],['gli',''],['','']].map(([a,g])=>[a,g,artVal(a,g)]);
  // recto / verso : un échantillon régulier + toutes les prépositions + tous les noms à article élidé
  const sample = words.filter((c,i)=>i%40===0 || /prep|postp/.test(c.pos||'') || /['’]$/.test(c.art||''));
  out.faces = [];
  for(const c of sample){
    const card = newCard({...c}, ''); card.lvl=c.lvl;
    for(const d of ['fr-de','de-fr']) for(const rv of [false,true]) for(const g of [null, c.art?(c.art==='der'||c.art==='il'?'die':'der'):null]){
      dir=d; revealed=rv; artGuess=g;
      try{ const f=cardFaces(card); out.faces.push([c.de, d, rv, g, f.front, f.back, f.reveal, f.showArtPick, cardTone(card)]); }
      catch(e){ out.faces.push([c.de, d, rv, g, 'ERREUR '+e.message]); }
    }
  }
  dir='fr-de'; revealed=false; artGuess=null;
  // écrans
  const first = (LISTDATA.A1||[]).slice(0,60).map(f=>newCard({...f}, 'b1'));
  first.forEach(c=>cards.set(c.id,c));
  out.views = {};
  renderList(); out.views.list = $('#view').innerHTML;
  renderAdd(); out.views.add = $('#view').innerHTML;
  const dq=$('#dq'); if(dq){ for(const q of (lang==='de'?['Hund','haus','Schluessel','partie','der Tisch']:['cane','casa',"l'amico",'partie','ville'])){ dq.value=q; dictSearch(); await new Promise(r=>setTimeout(r,30)); out.views['dict:'+q]=($('#dRes')||{}).innerHTML||''; } }
  // aperçu du pluriel et ajout d'un mot tapé à la main (article, genre déduit, dictionnaire)
  out.plPreview = []; out.added = [];
  const TYPED = lang==='de'
    ? [['Hund','-e','',''],['der Tisch','¨e','',''],['Kind','-er','das',''],['Auto','pl.','',''],['Lehrer','-','der','']]
    : [['cane','i cani','il|m',''],["l'amico",'gli amici','',''],["l'amica",'le amiche','',''],['casa','le case','la|f',''],['abate','gli abati','','']];
  for(const [w,pl,a] of TYPED){
    renderAdd(); $('#fDe').value=w; $('#fPl').value=pl; $('#fArt').value=a; plPreview(); out.plPreview.push([w,pl,a,($('#fPlPrev')||{}).innerHTML||'']);
    $('#fFr').value='zz '+w; const before=new Set(cards.keys());
    $('#addForm').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); await new Promise(r=>setTimeout(r,60));
    const nw=[...cards.values()].filter(c=>!before.has(c.id)).map(c=>[c.de,c.art,c.pl,c.g||'',c.fr,c.lang]);
    out.added.push([w, JSON.stringify(nw)]);
  }
  // voix : langue et vitesse de l'énoncé
  const said=[]; try{ speechSynthesis.speak=u=>said.push([u.lang, +u.rate.toFixed(3)]); SAY.speak('Test', lang); }catch(e){ said.push('ERREUR '+e.message); }
  out.tts = {said};
  renderStats(); await new Promise(r=>setTimeout(r,50)); out.views.stats = $('#view').innerHTML;
  // tri par la traduction, clés de comparaison des traductions, mots de même traduction
  const pool = words.slice(0, 3000).map((c,i)=>({...c, created:i}));
  out.sortFr = [...pool].sort(SORTS.fr).map(c=>c.de);
  out.sortDe = [...pool].sort(SORTS.de).map(c=>c.de);
  out.dupKeys = pool.map(c=>[c.fr, frDupKey(c.fr), frSortKey(c.fr)]);
  out.sameFr = sameFr(pool.slice(0,400).map(c=>({de:c.de+'x', art:c.art, fr:c.fr}))).length;
  renderGuide(); out.views.guide = $('#view').innerHTML;
  renderLangPick(); out.views.langpick = $('#view').innerHTML;
  out.meta = {code: L_().code, name: L_().name, adj: L_().adj, chars: L_().chars, pair: (document.getElementById('pair')||{}).textContent};
  return out;
}
"""


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    h = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


async def capture():
    res = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for lang in ('de', 'it'):
            pg = await b.new_page(viewport={'width': 390, 'height': 844})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script(INIT.replace('%LANG%', lang))
            await pg.goto(f'http://127.0.0.1:{PORT}/index.html')
            await pg.wait_for_timeout(1500)
            res[lang] = await pg.evaluate(PROBE, lang)
            res[lang]['errors'] = errs
            await pg.close()
        await b.close()
    return res


def diff(a, b, path=''):
    out = []
    if type(a) != type(b):
        return [f'{path}: type {type(a).__name__} ≠ {type(b).__name__}']
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f'{path}/{k}: absent d\'un côté')
            else:
                out += diff(a[k], b[k], f'{path}/{k}')
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f'{path}: {len(a)} ≠ {len(b)} éléments')
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f'{path}[{i}]')
    elif a != b:
        out.append(f'{path}:\n      avant : {str(a)[:300]}\n      après : {str(b)[:300]}')
    return out


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    srv = serve()
    res = asyncio.run(capture())
    srv.shutdown()
    for lang, r in res.items():
        print(f"{lang} : {len(r['words'])} mots, {len(r['faces'])} faces de carte, {len(r['views'])} écrans, "
              f"{len(r['caseVerdicts'])} verdicts de cas, erreurs JS : {len(r['errors'])}")
    if cmd == 'capture':
        json.dump(res, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
        print('référence enregistrée :', path)
        return
    ref = json.load(open(path, encoding='utf-8'))
    d = diff(ref, res)
    print(f'{len(d)} différence(s)')
    for x in d[:40]:
        print(' ', x)
    sys.exit(1 if d else 0)


if __name__ == '__main__':
    main()
