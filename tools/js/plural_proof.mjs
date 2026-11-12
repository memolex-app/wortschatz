// Preuve : pour chaque message converti, ancienne version (suffixe « s » si n>1) = nouvelle (Intl.PluralRules 'fr')
import fs from 'fs';
const proof = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const PR = new Intl.PluralRules('fr');
const plural = (forms, v) => { const f={}; forms.split('|').forEach(p=>{const e=p.indexOf('='); f[p.slice(0,e)]=p.slice(e+1);}); const c=PR.select(Number(v)); return f[c]!=null?f[c]:(f.other!=null?f.other:''); };
const newT = (m, a) => m.replace(/\{(\d+)(?::([^{}]*))?\}/g, (x,i,forms) => forms==null ? String(a[+i]) : plural(forms, a[+i]));
const oldT = (m, a) => m.replace(/\{(\d+)\}/g, (x,i) => String(a[+i]));
const N = [0, 1, 2, 3, 7, 21, 100, 1000000];
let checks = 0, bad = [];
for(const p of proof){
  const counts = [...new Set(p.args.map(x=>x.count).filter(x=>x!==undefined))];
  const combos = counts.reduce((acc, c) => acc.flatMap(o => N.map(n => ({...o, [c]: n}))), [{}]);
  for(const co of combos){
    const oldArgs = p.args.map((x,i) => x.plural ? (co[x.count] > 1 ? x.plural : '') : (i in co ? co[i] : `«A${i}»`));
    const newArgs = p.keep.map(i => oldArgs[i]);
    const o = oldT(p.old, oldArgs), n = newT(p.msg, newArgs); checks++;
    if(o !== n) bad.push({key: p.key, co, o, n});
  }
}
console.log(`${proof.length} messages, ${checks} combinaisons vérifiées, ${bad.length} différences`);
bad.slice(0,5).forEach(b=>console.log(b));
process.exit(bad.length ? 1 : 0);
