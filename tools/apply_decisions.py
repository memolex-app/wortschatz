"""Applique un fichier de décisions (nouvelles traductions de cartes) au format source data/.

Fichier : data/<L>-<U>/decisions/AAAA-MM-JJ-<nom>.tsv, colonnes : key · translation · reason
  key          clé de la carte (« der Teil », « auch »)
  translation  traduction complète de la carte (sens séparés par des virgules, notes entre parenthèses)
  reason       justification (source, règle de la procédure) ; non utilisée par l'outil

Effets :
  - les sens de la carte sont remplacés ; les identifiants « clé#n » existants sont gardés dans l'ordre,
    les sens en trop sont supprimés, les nouveaux reçoivent le numéro suivant ;
  - une traduction libre (cards.tsv) de la carte est retirée ;
  - une phrase d'exemple dont l'étiquette de sens ne correspond plus à aucun sens garde la phrase, sans étiquette
    (règle de la simplification d'octobre 2026).
Les fichiers de décisions sont appliqués par ordre de nom (date d'abord) ; un fichier déjà appliqué peut être
réappliqué sans effet.

Usage : python3 tools/apply_decisions.py de fr data/de-fr/decisions/2026-11-11-ambig-1.tsv [--dry]
"""
import os, re, sys
from mxdata import DATA, NONE, read_tsv, write_tsv, write_rows, split_senses, join_senses

ART = re.compile(r"^(?:(?:le|la|les|un|une|des|se)\s+|l'|s')", re.I)


def bare(s):
    """Sens sans note ni article, comme les étiquettes des phrases (« prestation de service »)."""
    s = re.sub(r'\s*\([^)]*\)', '', s).strip()
    return ART.sub('', s).strip().lower()


def apply(L, U, path, dry=False):
    d, p = os.path.join(DATA, L), os.path.join(DATA, f'{L}-{U}')
    lex = {r['key'] for r in read_tsv(f'{d}/lexemes.tsv')}
    senses = read_tsv(f'{d}/senses.tsv')
    glosses = {r['sense']: r['gloss'] for r in read_tsv(f'{p}/glosses.tsv')}
    cards = read_tsv(f'{p}/cards.tsv')
    ex_src = read_tsv(f'{d}/examples.tsv')
    ex_tr = read_tsv(f'{p}/examples.tsv')
    decisions = read_tsv(path)

    by_key = {}
    for s in senses:
        by_key.setdefault(s['key'], []).append(s['sense'])

    changed, unlabelled = [], 0
    for dec in decisions:
        k, fr = dec['key'], dec['translation'].strip()
        if k not in lex:
            raise SystemExit(f'carte inconnue : {k!r}')
        parts = split_senses(fr)
        if join_senses(parts) != fr:
            raise SystemExit(f'{k} : séparer les sens par « , » (« ; » seulement dans une note) : {fr!r}')
        old_ids = by_key.get(k, [])
        old = join_senses([glosses[s] for s in old_ids])
        if old == fr and not any(c['key'] == k for c in cards):
            continue
        used = {int(re.match(r'.*#(\d+)', s).group(1)) for s in old_ids if re.match(r'.*#\d+$', s)}
        nxt = max(used, default=0) + 1
        new_ids = []
        for i, g in enumerate(parts):
            if i < len(old_ids):
                sid = old_ids[i]
            else:
                sid = f'{k}#{nxt}'
                nxt += 1
            new_ids.append(sid)
            glosses[sid] = g
        for sid in old_ids[len(parts):]:
            glosses.pop(sid, None)
        by_key[k] = new_ids
        cards = [c for c in cards if c['key'] != k]
        changed.append((k, old, fr))

        # étiquettes des phrases de cette carte
        keep = {bare(g) for g in parts}
        ids = {e['id'] for e in ex_src if e['key'] == k}
        for t in ex_tr:
            if t['id'] in ids and t['sense_label'] not in (NONE, '') and bare(t['sense_label']) not in keep:
                t['sense_label'] = ''
                unlabelled += 1

    if not dry:
        order = [r['key'] for r in read_tsv(f'{d}/lexemes.tsv')]
        new_senses = [[sid, k] for k in order for sid in by_key.get(k, [])]
        write_tsv(f'{d}/senses.tsv', ['sense', 'key'], new_senses)
        write_tsv(f'{p}/glosses.tsv', ['sense', 'gloss'], [[sid, glosses[sid]] for sid, _ in new_senses])
        write_tsv(f'{p}/cards.tsv', ['key', 'translation'], [[c['key'], c['translation']] for c in cards])
        write_rows(f'{p}/examples.tsv', ex_tr, ['id', 'translation', 'sense_label'])
    for k, o, n in changed:
        print(f'{k} : {o}  →  {n}')
    print(f'{len(changed)} cartes modifiées, {unlabelled} phrases sans étiquette de sens'
          + (' (essai, rien écrit)' if dry else ''))


if __name__ == '__main__':
    apply(sys.argv[1], sys.argv[2], sys.argv[3], '--dry' in sys.argv)
