// Convertit les suffixes de pluriel des messages : « carte{1} » (valeur « s » ou rien) → « {0:one=carte|other=cartes} »
// Usage : node plural_convert.mjs index.html i18n/fr.json preuve.json
import * as acorn from 'acorn';
import fs from 'fs';
const [htmlPath, frPath, proofPath] = process.argv.slice(2);
let html = fs.readFileSync(htmlPath, 'utf8');
const fr = JSON.parse(fs.readFileSync(frPath, 'utf8'));
const proof = [];
let total = 0, pass = 0;
for(;;){ pass++;
const a = html.indexOf('<script>') + 8, b = html.indexOf('</script>', a);
const js = html.slice(a, b);
const ast = acorn.parse(js, {ecmaVersion: 'latest'});
const calls = [];
(function walk(n){
  if(!n || typeof n.type !== 'string') return;
  if(n.type==='CallExpression' && n.callee.type==='Identifier' && n.callee.name==='T' && n.arguments.length===2
     && n.arguments[0].type==='Literal' && n.arguments[1].type==='ArrayExpression'){
    const args = n.arguments[1].elements.map(e => {
      const pl = e.type==='ConditionalExpression' && e.test.type==='BinaryExpression' && e.test.operator==='>' &&
        e.test.right.type==='Literal' && e.test.right.value===1 && e.consequent.type==='Literal' && ['s','x'].includes(e.consequent.value) &&
        e.alternate.type==='Literal' && e.alternate.value==='';
      return {src: js.slice(e.start, e.end), plural: pl ? {count: js.slice(e.test.left.start, e.test.left.end).replace(/\s/g,''), suffix: e.consequent.value} : null};
    });
    if(args.some(x=>x.plural)) calls.push({key: n.arguments[0].value, arr: [n.arguments[1].start, n.arguments[1].end], args});
  }
  for(const k in n){ const v=n[k]; if(Array.isArray(v)) v.forEach(walk); else if(v && typeof v.type==='string') walk(v); }
})(ast);
const edits = [], problems = [];
// appels les plus intérieurs seulement : aucun autre appel à convertir dans leur tableau
const inner = calls.filter(c => !calls.some(d => d !== c && d.arr[0] >= c.arr[0] && d.arr[1] <= c.arr[1]));
if(!inner.length) break;
for(const c of inner){
  const old = fr[c.key];
  // index du nombre pour chaque suffixe
  const countIdx = c.args.map(x => x.plural ? c.args.findIndex(y => !y.plural && y.src.replace(/\s/g,'') === x.plural.count) : null);
  if(countIdx.some((j,i)=>c.args[i].plural && j<0)){ problems.push(c.key); continue; }
  const keep = c.args.map((x,i)=>!x.plural ? i : null).filter(i=>i!==null);
  const renum = Object.fromEntries(keep.map((i,n)=>[i,n]));
  let msg = old;
  // mot + {k} → {j:one=mot|other=mot+suffixe}
  c.args.forEach((x,k)=>{
    if(!x.plural) return;
    const re = new RegExp(`([\\p{L}’']+)\\{${k}\\}`, 'u');
    const m = msg.match(re);
    if(!m){ problems.push(c.key+' {'+k+'}'); return; }
    msg = msg.replace(re, `{${countIdx[k]}§:one=${m[1]}|other=${m[1]}${x.plural.suffix}}`);
  });
  // renuméroter : {i} et {i§:…} (le § protège les blocs déjà convertis), puis retirer §
  msg = msg.replace(/\{(\d+)(§?)(:[^{}]*)?\}/g, (all, i, mark, rest) => {
    const n = renum[+i]; if(n===undefined) throw new Error(c.key+' : emplacement {'+i+'} supprimé encore présent');
    return `{${n}${rest||''}}`;
  });
  proof.push({key: c.key, old, msg, args: c.args.map(x=>x.plural ? {plural: x.plural.suffix, count: countIdx[c.args.indexOf(x)]} : {}), keep});
  fr[c.key] = msg;
  edits.push({start: a + c.arr[0], end: a + c.arr[1], src: '[' + keep.map(i=>c.args[i].src).join(',') + ']'});
}
if(problems.length){ console.error('problèmes :', problems); process.exit(1); }
edits.sort((x,y)=>y.start-x.start).forEach(e=>{ html = html.slice(0,e.start) + e.src + html.slice(e.end); });
total += inner.length; console.log(`passe ${pass} : ${inner.length} messages`);
}
fs.writeFileSync(htmlPath, html); fs.writeFileSync(frPath, JSON.stringify(fr, null, 1));
fs.writeFileSync(proofPath, JSON.stringify(proof));
console.log(`${total} messages convertis`);
