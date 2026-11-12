"""Contrôle des traductions de l'interface : i18n/<langue>.json comparé à i18n/fr.json (référence).

Pour chaque message traduit :
  - clé connue en français ;
  - mêmes emplacements {n} (chaque valeur insérée doit apparaître ; un emplacement inconnu casserait l'affichage) ;
  - mêmes nombres pour les pluriels {n:…}, et chaque pluriel a une forme « other » ;
  - mêmes balises HTML (nom et nombre), même nombre d'entités (&#10;…).
Signale aussi les messages non traduits (ils s'afficheront en français).
Usage : python3 tools/i18n_check.py [langue…]     code 1 s'il y a une erreur
"""
import collections, glob, json, os, re, sys
from mxdata import ROOT

PH = re.compile(r'\{(\d+)(?::([^{}]*))?\}')
TAG = re.compile(r'<\s*(/?)\s*([a-zA-Z][\w-]*)')


def shape(m):
    simple = sorted({int(i) for i, f in PH.findall(m) if not f})
    plural = sorted({int(i) for i, f in PH.findall(m) if f})
    tags = collections.Counter((c + n.lower()) for c, n in TAG.findall(m))
    ents = len(re.findall(r'&#?\w+;', m))
    return simple, plural, tags, ents


def check(lang, fr, tr):
    errors, missing = [], [k for k in fr if k not in tr]
    for k, m in tr.items():
        if k not in fr:
            errors.append(f'{k} : clé inconnue en français'); continue
        if not isinstance(m, str):
            errors.append(f'{k} : message non textuel'); continue
        a, b = shape(fr[k]), shape(m)
        if a[0] != b[0]:
            errors.append(f'{k} : emplacements {a[0]} attendus, {b[0]} trouvés')
        if a[1] != b[1]:
            errors.append(f'{k} : pluriels sur {a[1]} attendus, {b[1]} trouvés')
        for i, forms in PH.findall(m):
            if forms and not re.search(r'(^|\|)other=', forms):
                errors.append(f'{k} : pluriel {{{i}}} sans forme « other »')
        if a[2] != b[2]:
            errors.append(f'{k} : balises {dict(a[2])} attendues, {dict(b[2])} trouvées')
        if a[3] != b[3]:
            errors.append(f'{k} : {a[3]} entités HTML attendues, {b[3]}')
    return errors, missing


def main():
    fr = json.load(open(os.path.join(ROOT, 'i18n', 'fr.json'), encoding='utf-8'))
    langs = sys.argv[1:] or [os.path.basename(p)[:-5] for p in sorted(glob.glob(os.path.join(ROOT, 'i18n', '*.json')))
                             if not p.endswith('/fr.json')]
    bad = False
    for l in langs:
        tr = json.load(open(os.path.join(ROOT, 'i18n', f'{l}.json'), encoding='utf-8'))
        errors, missing = check(l, fr, tr)
        print(f'{l} : {len(tr)} messages, {len(errors)} erreurs, {len(missing)} non traduits ({100 * (len(fr) - len(missing)) / len(fr):.0f} % traduit)')
        for e in errors[:30]:
            print('   ', e)
        bad |= bool(errors)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
