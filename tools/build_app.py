"""Injecte la description des langues (data/<L>/langue.json) dans l'appli (index.html).

La description d'une langue (articles, genres, élision, style du pluriel, cas, lettres, voix, recherche tolérante,
textes d'aide liés à la langue) est la seule référence ; index.html en reçoit une copie entre deux balises :
  /* LANG_DATA:BEGIN (généré par tools/build_app.py, ne pas éditer) */ … /* LANG_DATA:END */
Les langues apparaissent dans l'ordre de leur champ « order ».

Usage :
  python3 tools/build_app.py           met à jour index.html
  python3 tools/build_app.py --check   vérifie que index.html est à jour (code 1 sinon)
"""
import glob, json, os, re, sys
from mxdata import ROOT, DATA

BEGIN = '/* LANG_DATA:BEGIN (généré par tools/build_app.py, ne pas éditer) */'
END = '/* LANG_DATA:END */'
REQUIRED = ['order', 'code', 'name', 'adj', 'articles', 'plural', 'tts', 'chars', 'charsUp']


def collect():
    langs = []
    for p in sorted(glob.glob(os.path.join(DATA, '*', 'langue.json'))):
        code = os.path.basename(os.path.dirname(p))
        d = json.load(open(p, encoding='utf-8'))
        miss = [k for k in REQUIRED if k not in d]
        if miss:
            raise SystemExit(f'{p} : champs manquants {miss}')
        if d['plural'] not in ('suffix', 'full'):
            raise SystemExit(f'{p} : plural doit valoir « suffix » ou « full »')
        langs.append((d['order'], code, d))
    return {code: d for _, code, d in sorted(langs)}


def block(langs):
    return f"{BEGIN}\nconst LANG_DATA = {json.dumps(langs, ensure_ascii=False, separators=(',', ':'))};\n{END}"


def main():
    path = os.path.join(ROOT, 'index.html')
    src = open(path, encoding='utf-8').read()
    m = re.search(re.escape(BEGIN) + r'.*?' + re.escape(END), src, re.S)
    if not m:
        raise SystemExit('balises LANG_DATA absentes de index.html')
    new = src[:m.start()] + block(collect()) + src[m.end():]
    if '--check' in sys.argv:
        ok = new == src
        print('index.html à jour' if ok else 'index.html PAS à jour : lancer tools/build_app.py')
        sys.exit(0 if ok else 1)
    open(path, 'w', encoding='utf-8').write(new)
    print('index.html : description des langues injectée (' + ', '.join(collect()) + ')')


if __name__ == '__main__':
    main()
