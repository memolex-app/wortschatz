"""Chargement des données Memolex (paire italien -> français) depuis les JSON publiés.
Usage : from common import load ; cards, ex, chunks = load('/chemin/vers/depot')
"""
import json, os, re, sys
REPO = os.environ.get('MEMOLEX_REPO', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def load(repo=REPO, pair='it-fr'):
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
    return (art + w) if art else w

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


def ignored(tool, w, sentence, base=os.path.dirname(os.path.abspath(__file__))):
    """Faux positifs déjà vérifiés à la main : lignes « mot|phrase italienne » de ignore_<outil>.txt."""
    p = os.path.join(base, f'ignore_{tool}.txt')
    if not os.path.exists(p): return False
    return f'{w}|{sentence}' in {l.rstrip('\n') for l in open(p, encoding='utf-8')}
