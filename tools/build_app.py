"""Injecte la description des langues dans l'appli (index.html) :
  data/<L>/langue.json        langue apprise (bloc LANG_DATA)
  data/<U>/utilisateur.json   langue de l'utilisateur : articles à ignorer pour comparer et trier, notes
                              grammaticales, format des dates et nombres, sens de l'écriture (bloc USER_DATA)

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

# (fichier de description, nom du bloc, champs obligatoires)
BLOCKS = [('langue.json', 'LANG_DATA', ['order', 'code', 'name', 'adj', 'articles', 'plural', 'tts', 'chars', 'charsUp']),
          ('utilisateur.json', 'USER_DATA', ['order', 'code', 'name', 'locale', 'dir', 'articles', 'elided', 'gramNoteWords'])]
begin = lambda n: f'/* {n}:BEGIN (généré par tools/build_app.py, ne pas éditer) */'
end = lambda n: f'/* {n}:END */'


def collect(fname, required):
    langs = []
    for p in sorted(glob.glob(os.path.join(DATA, '*', fname))):
        code = os.path.basename(os.path.dirname(p))
        d = json.load(open(p, encoding='utf-8'))
        miss = [k for k in required if k not in d]
        if miss:
            raise SystemExit(f'{p} : champs manquants {miss}')
        if fname == 'langue.json' and d['plural'] not in ('suffix', 'full'):
            raise SystemExit(f'{p} : plural doit valoir « suffix » ou « full »')
        langs.append((d['order'], code, d))
    return {code: d for _, code, d in sorted(langs)}


def block(name, langs):
    return f"{begin(name)}\nconst {name} = {json.dumps(langs, ensure_ascii=False, separators=(',', ':'))};\n{end(name)}"


def main():
    path = os.path.join(ROOT, 'index.html')
    src = open(path, encoding='utf-8').read()
    new = src
    for fname, name, req in BLOCKS:
        m = re.search(re.escape(begin(name)) + r'.*?' + re.escape(end(name)), new, re.S)
        if not m:
            raise SystemExit(f'balises {name} absentes de index.html')
        new = new[:m.start()] + block(name, collect(fname, req)) + new[m.end():]
    if '--check' in sys.argv:
        ok = new == src
        print('index.html à jour' if ok else 'index.html PAS à jour : lancer tools/build_app.py')
        sys.exit(0 if ok else 1)
    open(path, 'w', encoding='utf-8').write(new)
    print('index.html : descriptions injectées — apprises : ' + ', '.join(collect(*BLOCKS[0][::2]))
          + ' ; de l\'utilisateur : ' + ', '.join(collect(*BLOCKS[1][::2])))


if __name__ == '__main__':
    main()
