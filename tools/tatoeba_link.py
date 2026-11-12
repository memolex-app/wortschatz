"""Rattache chaque phrase d'exemple et sa traduction à leur numéro Tatoeba et à leur auteur.

Usage : python3 tools/tatoeba_link.py de fr /chemin/vers/exports_tatoeba [--dry]
Exports attendus (https://downloads.tatoeba.org/exports/per_language/) :
  <l3>_sentences_detailed.tsv (id, langue, texte, auteur, ajout, modification) pour la langue apprise et celle de l'utilisateur,
  <l3>-<u3>_links.tsv (id, id traduit).
Ajoute les colonnes « tatoeba » et « author » à data/<L>/examples.tsv (phrase) et data/<L>-<U>/examples.tsv (traduction).
Exception : data/<L>/tatoeba_manual.tsv donne le numéro d'une phrase gardée dans une version différente de celle de Tatoeba.
Choix quand une phrase existe plusieurs fois sur Tatoeba : la paire citée dans les crédits publiés, puis une paire
liée sur Tatoeba, puis le numéro le plus ancien. Les phrases rédigées pour Memolex (origin = mx) ne sont pas rattachées.
"""
import json, os, re, sys, unicodedata
from mxdata import ROOT, DATA, read_tsv, write_tsv

L3 = {'de': 'deu', 'fr': 'fra', 'it': 'ita', 'en': 'eng', 'es': 'spa'}


def norm(s):
    """Comparaison tolérante : typographie normalisée par Memolex (apostrophes, ligatures, ß des corrections)."""
    s = unicodedata.normalize('NFC', s)
    s = s.replace('’', "'").replace('‘', "'").replace('ʼ', "'").replace('œ', 'oe').replace('Œ', 'Oe')
    s = s.replace('æ', 'ae').replace(' ', ' ').replace(' ', ' ').replace('ß', 'ss')
    s = s.replace('«', '"').replace('»', '"').replace('„', '"').replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip()


def sentences(path):
    by_text, author = {}, {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 4:
                continue
            i = int(p[0])
            by_text.setdefault(norm(p[2]), []).append(i)
            author[i] = '' if p[3] == '\\N' else p[3]
    return by_text, author


def links(path):
    out = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            a, b = line.split('\t')[:2]
            out.add((int(a), int(b)))
    return out


def run(L, U, tdir, dry=False):
    l3, u3 = L3[L], L3[U]
    lt, la = sentences(os.path.join(tdir, f'{l3}_sentences_detailed.tsv'))
    ut, ua = sentences(os.path.join(tdir, f'{u3}_sentences_detailed.tsv'))
    lk = links(os.path.join(tdir, f'{l3}-{u3}_links.tsv'))
    cred = json.load(open(os.path.join(ROOT, f'credits-{L}-{U}.json'), encoding='utf-8'))
    credited = {(c[0], c[2]) for c in cred['c']}
    cl = {c[0] for c in cred['c']}
    cu = {c[2] for c in cred['c']}

    d, p = os.path.join(DATA, L), os.path.join(DATA, f'{L}-{U}')
    src = read_tsv(f'{d}/examples.tsv')
    tr = {t['id']: t for t in read_tsv(f'{p}/examples.tsv')}
    manual = {r['sentence']: int(r['tatoeba']) for r in read_tsv(f'{d}/tatoeba_manual.tsv')}   # phrase modifiée depuis sur Tatoeba
    stats = dict(total=0, both=0, credited=0, linked=0, nol=0, nou=0)
    missing = []
    for e in src:
        t = tr.get(e['id'])
        e.setdefault('tatoeba', ''); e.setdefault('author', '')
        if t is not None:
            t.setdefault('tatoeba', ''); t.setdefault('author', '')
        if e['origin'] == 'mx' or t is None:
            continue
        stats['total'] += 1
        L_ids = [manual[e['sentence']]] if e['sentence'] in manual else lt.get(norm(e['sentence']), [])
        U_ids = ut.get(norm(t['translation']), [])
        pairs = [(a, b) for a in L_ids for b in U_ids]
        pick = next((x for x in pairs if x in credited), None)
        if pick:
            stats['credited'] += 1
        else:
            pick = next((x for x in pairs if x in lk), None)
            if pick:
                stats['linked'] += 1
        if pick:
            li, ui = pick
        else:
            li = next((i for i in L_ids if i in cl), min(L_ids) if L_ids else None)
            ui = next((i for i in U_ids if i in cu), min(U_ids) if U_ids else None)
        if li is None: stats['nol'] += 1
        if ui is None: stats['nou'] += 1
        if li and ui: stats['both'] += 1
        else: missing.append((e['key'], e['sentence'], t['translation'], li, ui))
        e['tatoeba'], e['author'] = (str(li), la[li]) if li else ('', '')
        t['tatoeba'], t['author'] = (str(ui), ua[ui]) if ui else ('', '')

    n = stats['total']
    print(f"{L}-{U} : {n} phrases Tatoeba ; rattachées des deux côtés : {stats['both']} ({100*stats['both']/max(n,1):.2f} %)")
    print(f"  dont paire des crédits : {stats['credited']}, paire liée sur Tatoeba : {stats['linked']} ;"
          f" phrase introuvable : {stats['nol']}, traduction introuvable : {stats['nou']}")
    for m in missing[:40]:
        print('  ?', m)
    if not dry:
        write_tsv(f'{d}/examples.tsv', ['id', 'key', 'sentence', 'highlight', 'origin', 'tatoeba', 'author'],
                  [[e[k] for k in ('id', 'key', 'sentence', 'highlight', 'origin', 'tatoeba', 'author')] for e in src])
        rows = read_tsv(f'{p}/examples.tsv')
        write_tsv(f'{p}/examples.tsv', ['id', 'translation', 'sense_label', 'tatoeba', 'author'],
                  [[tr[r['id']][k] if k in tr[r['id']] else '' for k in ('id', 'translation', 'sense_label', 'tatoeba', 'author')]
                   for r in rows])
    return missing


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3], '--dry' in sys.argv)
