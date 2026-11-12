"""Chargement des données Memolex d'une paire, pour les contrôles.
Par défaut : format source data/ (via build.py, en mémoire). MX_SOURCE=json : fichiers JSON publiés.
Paire : variable MX_PAIR (« de-fr », « it-fr »… ; défaut it-fr, historique).
Usage : from common import load ; cards, ex, chunks = load()
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get('MEMOLEX_REPO', os.path.join(HERE, '..'))
PAIR = os.environ.get('MX_PAIR', 'it-fr')
SOURCE = os.environ.get('MX_SOURCE', 'data')

def load(repo=REPO, pair=None):
    pair = pair or PAIR
    if SOURCE == 'data':
        sys.path.insert(0, HERE)
        from build import build
        L, U = pair.split('-')
        b = build(L, U)
        lists, ex, chunks = b['lists'], b['examples'], b['chunks']
    else:
        if not os.path.exists(os.path.join(repo, f'lists-{pair}.json')):
            repo = REPO
        lists = json.load(open(os.path.join(repo, f'lists-{pair}.json')))
        ex = json.load(open(os.path.join(repo, f'examples-{pair}.json')))
        chunks = json.load(open(os.path.join(repo, f'chunks-{pair}.json')))
    cards = []
    for i, r in enumerate(lists):
        lv, w, nat, art, pl, fr = r[:6]
        gender = r[6] if len(r) > 6 else ''
        cards.append(dict(i=i + 1, lv=lv, w=w, nat=nat, art=art, pl=pl, fr=fr, g=gender,
                          key=ex_key(art, w)))
    return cards, ex, chunks

def ex_key(art, w):
    # clé des exemples : article + mot, sans espace (« ilmarzo », « l'anno ») ; sans article : le mot seul
    # (en minuscules, comme l'appli : « derunternehmer »)
    return (art + w).lower()

def shown(c):
    a = c['art']
    return (a + c['w']) if a.endswith("'") else ((a + ' ' + c['w']) if a else c['w'])

def strip_note(s):
    return re.sub(r'\s*\([^)]*\)', '', s).strip()

def fr_senses(fr):
    """Traductions d'une carte : séparées par virgule ou point-virgule, notes retirées, article français retiré."""
    out = []
    for part in re.split(r'[;,]', strip_note(fr)):
        p = part.strip()
        p = re.sub(r"^(?:(?:le|la|les|un|une|des|se)\s+|l'|s')", '', p, flags=re.I).strip()
        if p: out.append(p)
    return out


_IGN = {}
def ignored(tool, w, sentence, base=HERE):
    """Faux positifs déjà vérifiés à la main : lignes « mot|phrase » de ignore_<outil>_<paire>.txt
    (texte après « # » ignoré : justification)."""
    if tool not in _IGN:
        p = os.path.join(base, f'ignore_{tool}_{PAIR}.txt')
        _IGN[tool] = {l.split(' #')[0].rstrip('\n').rstrip() for l in open(p, encoding='utf-8')} if os.path.exists(p) else set()
    return f'{w}|{sentence}' in _IGN[tool]
