"""Fusionne des sens d'un mot (décision sur la langue apprise) : deux traductions synonymes d'un même sens.

Fichier : data/<L>/decisions/AAAA-MM-JJ-<nom>.tsv, colonnes : key · groups · reason
  groups   regroupement des sens actuels du mot, par position : « 1+2 » (un seul sens), « 1+2|3 » (deux sens)
Le sens fusionné garde l'identifiant du premier ; dans chaque paire data/<L>-*/glosses.tsv, il reçoit les traductions
des sens fusionnés, dans le même ordre. Les groupes doivent suivre l'ordre des sens : la traduction affichée d'une carte
(sens joints par des virgules) ne change donc pas. Réappliquer un fichier déjà appliqué est sans effet
(un mot qui n'a plus le nombre de sens attendu est signalé et laissé tel quel).
Usage : python3 tools/apply_sense_merges.py de data/de/decisions/2026-11-12-sens.tsv [--dry]
"""
import glob, os, sys
from mxdata import DATA, read_tsv, write_tsv


def apply(L, path, dry=False):
    d = os.path.join(DATA, L)
    senses = read_tsv(f'{d}/senses.tsv')
    by_key = {}
    for s in senses:
        by_key.setdefault(s['key'], []).append(s['sense'])
    remap, merged, skipped = {}, 0, []      # sens supprimé → sens qui le reçoit
    for dec in read_tsv(path):
        ids = by_key.get(dec['key'])
        groups = [[int(x) for x in g.split('+')] for g in dec['groups'].split('|')]
        flat = [x for g in groups for x in g]
        if ids is None or flat != list(range(1, len(ids) + 1)):
            skipped.append(dec['key']); continue
        new = []
        for g in groups:
            head = ids[g[0] - 1]
            new.append(head)
            for x in g[1:]:
                remap[ids[x - 1]] = head
        by_key[dec['key']] = new
        merged += 1
    print(f'{merged} mots regroupés, {len(remap)} sens fusionnés' + (f', {len(skipped)} ignorés (déjà faits ou changés) : {skipped[:5]}' if skipped else '')
          + (' (essai, rien écrit)' if dry else ''))
    if dry or not remap:
        return
    order = [r['key'] for r in read_tsv(f'{d}/lexemes.tsv')]
    write_tsv(f'{d}/senses.tsv', ['sense', 'key'], [[sid, k] for k in order for sid in by_key.get(k, [])])
    for p in glob.glob(os.path.join(DATA, f'{L}-*', 'glosses.tsv')):
        rows = read_tsv(p)
        # les traductions gardent leur ordre ; seules changent les étiquettes de sens
        write_tsv(p, ['sense', 'gloss'], [[remap.get(r['sense'], r['sense']), r['gloss']] for r in rows])


if __name__ == '__main__':
    apply(sys.argv[1], sys.argv[2], '--dry' in sys.argv)
