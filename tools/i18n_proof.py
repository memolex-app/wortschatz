"""Preuve d'équivalence de l'extraction des textes (i18n_extract.py), et valeurs exactes de i18n/fr.json.

Pour chaque texte remplacé, le navigateur évalue le littéral JavaScript d'origine ('…', "…" ou `…`) ; toutes les
occurrences d'une clé doivent donner la même valeur, et cette valeur est écrite dans i18n/fr.json.
Ainsi t('clé') renvoie exactement la chaîne d'origine, partout dans l'appli.
Usage : python3 tools/i18n_proof.py /chemin/i18n_proof.json [--write]
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
from mxdata import ROOT


async def evaluate(raws):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        vals = await pg.evaluate("raws => raws.map(r => { try { return (0, eval)(r); } catch(e) { return {err: String(e)}; } })", raws)
        await b.close()
    return vals


def main():
    proof = json.load(open(sys.argv[1], encoding='utf-8'))
    vals = asyncio.run(evaluate([raw for _, raw in proof]))
    path = os.path.join(ROOT, 'i18n', 'fr.json')
    fr = json.load(open(path, encoding='utf-8'))
    exact, bad = {}, []
    for (k, raw), v in zip(proof, vals):
        if isinstance(v, dict):
            bad.append((k, raw, v['err'])); continue
        if k in exact and exact[k] != v:
            bad.append((k, raw, f'valeur différente d\'une autre occurrence : {exact[k]!r} ≠ {v!r}')); continue
        exact[k] = v
    approx = [k for k in exact if fr.get(k) is not None and fr[k] != exact[k]]
    print(f'{len(proof)} occurrences, {len(exact)} clés ; erreurs : {len(bad)} ; valeurs corrigées par le navigateur : {len(approx)}')
    for b in bad[:20]:
        print('  ', b)
    if set(exact) != set(fr):
        print('  clés sans occurrence ou occurrences sans clé :', sorted(set(exact) ^ set(fr))[:10]); bad.append('clés')
    if '--write' in sys.argv and not bad:
        json.dump({k: exact[k] for k in fr}, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('i18n/fr.json : valeurs exactes écrites')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
