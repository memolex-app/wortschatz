"""Lance tous les contrôles d'une paire sur le format source data/.

Usage :
  python3 tools/check.py de fr            contrôles rapides
  python3 tools/check.py de fr --full     + contrôles des phrases d'exemple (spaCy, plusieurs minutes)
  python3 tools/check.py de fr --compare  chaque contrôle lancé sur data/ ET sur les JSON publiés : sorties identiques attendues
Code de sortie 1 si une sortie diffère (--compare).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# contrôles selon la langue de l'utilisateur : check_dups et chunks_check lisent les articles dans data/<U>/utilisateur.json
# (le contrôle de sens des chunks, --sens, reste écrit pour le français) ; register et ex_gloss sont propres au français
FOR_USER = {'fr': ['check_dups', 'chunks_check', 'register'], 'en': ['check_dups', 'chunks_check'], 'it': ['check_dups', 'chunks_check']}
FOR_USER_FULL = {'fr': ['ex_gloss']}
# contrôles propres à la langue apprise
FOR_LANG = {'it': ['plural_check'], 'de': ['prep_case']}
FOR_LANG_FULL = {'it': ['ex_pos'], 'de': ['ex_form_de']}
# contrôles propres à la paire (catalogue)
FOR_PAIR = {'it-fr': ['faux_amis'], 'de-fr': ['faux_amis']}


def run(script, pair, source):
    env = dict(os.environ, MX_PAIR=pair, MX_SOURCE=source)
    p = subprocess.run([sys.executable, os.path.join(HERE, script + '.py')], cwd=HERE, env=env,
                       capture_output=True, text=True)
    return (p.stdout + p.stderr).strip()


def main():
    L, U = sys.argv[1], sys.argv[2]
    pair, full, compare = f'{L}-{U}', '--full' in sys.argv, '--compare' in sys.argv
    todo = FOR_USER.get(U, []) + FOR_LANG.get(L, []) + FOR_PAIR.get(pair, [])
    if full:
        todo += FOR_USER_FULL.get(U, []) + FOR_LANG_FULL.get(L, [])
    same = True
    for s in todo:
        out = run(s, pair, 'data')
        lines = out.splitlines()
        head = lines[0] if lines else '0 alerte'
        if s == 'faux_amis':
            head = f'{len(lines)} faux amis signalés'
        tag = ''
        if compare:
            ok = out == run(s, pair, 'json')
            same &= ok
            tag = '  [data = json]' if ok else '  [DIFFÉRENT de json]'
        print(f'== {s}: {head}{tag}')
        for l in (lines if s == 'faux_amis' else lines[1:])[:60]:
            print('   ', l)
    if compare and not same:
        sys.exit(1)


if __name__ == '__main__':
    main()
