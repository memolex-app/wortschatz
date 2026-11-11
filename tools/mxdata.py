"""Memolex : format source multilingue (données/) <-> fichiers publiés (*-xx-yy.json).

Le format source est la seule référence à éditer. Les JSON lus par l'appli en sont générés par build.py.
Voir docs/conception-multilingue.md.

Fichiers (TSV, UTF-8, une ligne par élément, première ligne = en-têtes) :
  data/<L>/lexemes.tsv        un mot de la langue apprise L (ordre = ordre des listes)
  data/<L>/senses.tsv         les sens de chaque mot (identifiant stable « clé#n »)
  data/<L>/chunks.tsv         l'expression « À retenir » (dans la langue L)
  data/<L>/examples.tsv       les phrases d'exemple (dans la langue L)
  data/<L>-<U>/glosses.tsv    traduction de chaque sens dans la langue de l'utilisateur U
  data/<L>-<U>/cards.tsv      traduction complète d'une carte quand elle ne se déduit pas des sens (rare)
  data/<L>-<U>/chunks.tsv     traduction des chunks
  data/<L>-<U>/examples.tsv   traduction des phrases (+ étiquette du sens illustré)
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
DATA = os.path.join(ROOT, 'data')
NONE = '~'  # champ absent (distinct d'un champ vide), pour reproduire les fichiers à l'identique


def card_key(art, word):
    """Clé d'unicité d'un mot : article + mot de la langue apprise (« das Gericht », « essen »)."""
    return f'{art} {word}' if art and not art.endswith("'") else f'{art}{word}'


def app_key(art, word):
    """Clé utilisée par l'appli dans examples-/chunks- (minuscules, sans espace : « dasgericht »)."""
    return (art + word).lower()


def split_senses(fr):
    """Découpe une traduction en sens : virgule ou point-virgule hors parenthèses.
    Les notes restent collées à leur sens (« autour de (lieu), à (heure) »)."""
    out, depth, cur = [], 0, ''
    for ch in fr:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if depth == 0 and ch in ',;':
            out.append(cur.strip())
            cur = ''
            continue
        cur += ch
    out.append(cur.strip())
    return [s for s in out if s]


def join_senses(senses):
    return ', '.join(senses)


# ---------- TSV ----------

def write_tsv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar='\\')
        w.writerow(header)
        for r in rows:
            for v in r:
                if '\t' in str(v) or '\n' in str(v):
                    raise ValueError(f'tabulation ou retour à la ligne interdit : {r!r}')
            w.writerow(r)


def read_tsv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
        head = next(r)
        return [dict(zip(head, row)) for row in r]


def dump(obj):
    """Écriture des JSON publiés : compacte, sans retour à la ligne final (format historique)."""
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
