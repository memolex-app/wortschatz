"""Extraction (une fois) des textes français de l'appli vers i18n/fr.json.

Analyse le script de index.html (analyseur lexical JavaScript simplifié : commentaires, chaînes, expressions
régulières, gabarits `…${}…` imbriqués) et remplace :
  - une chaîne '…' ou "…" de texte français                      → T('clé')
  - dans un gabarit, une phrase (texte + balises de mise en forme + valeurs insérées), découpée aux balises de bloc
    (div, p, li, button…)                                          → ${T('clé', [valeur0, valeur1…])}
    message : « <b>{0} mots en cours</b> … au-delà de {1} : … »
  - la valeur d'un attribut lisible (placeholder, aria-label, title, alt) : même traitement.
Les valeurs insérées sont recopiées dans l'ordre : elles sont évaluées dans le même ordre qu'avant.
Non touchés : blocs générés (LANG_DATA, USER_DATA), commentaires, guide (renderGuide : étape 5.3).

Sorties : index.html, i18n/fr.json (clé → message), i18n/contexte.tsv (aide aux traducteurs),
$I18N_PROOF (code d'origine de chaque message, pour la preuve d'équivalence : tools/i18n_proof.py).
Usage : python3 tools/i18n_extract.py [--dry]
"""
import glob, json, os, re, sys, unicodedata
from mxdata import ROOT, DATA, read_tsv

ACCENT = re.compile(r"[àâçéèêëîïôûùÿœæÀÂÇÉÈÊËÎÏÔÛÙŒ…’«»]")      # accents français (pas ä, ö, ß)
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿœŒ]{2,}")
NOT_TEXT = {'Enter', 'Escape', 'Tab', 'Backspace', 'Space', 'Shift', 'Control', 'Meta', 'Alt', 'Delete', 'Home',
            'End', 'Memolex', 'Tatoeba', 'Supabase', 'Google', 'Android', 'Chrome', 'Safari', 'Firefox', 'Error',
            'Gen', 'Akk', 'Dat'}
REGEX_PREV = set('(,=:[!&|?{};+-*%<>~^') | {''}
REGEX_KW = {'return', 'typeof', 'case', 'in', 'of', 'delete', 'void', 'throw', 'new', 'else', 'do'}
INLINE = {'b', 'i', 'em', 'strong', 'small', 'span', 'code', 'a', 'u', 'sup', 'sub', 'br', 'mark', 'kbd', 'abbr', 'q'}
READABLE_ATTR = {'placeholder', 'aria-label', 'title', 'alt'}
SKIP_FUNCS = set(os.environ.get('I18N_SKIP', '').split(',')) - {''}   # guide extrait à l'étape 5.3
# tables d'étiquettes dont les valeurs sont des mots isolés en minuscules (« nom », « masculin ») : extraites quand même
FORCE_CONSTS = {'GENRE', 'POS_LABEL'}


def _vocab():
    v = set()
    for f in glob.glob(os.path.join(DATA, '*-fr', '*.tsv')):
        for r in read_tsv(f):
            for x in r.values():
                v.update(w.lower() for w in WORD.findall(x or ''))
    v.update('à au aux de des du en et la le les un une ou où ne pas plus tu te ton ta tes ici déjà'.split())
    return v - {'class', 'type', 'data', 'style', 'width', 'button', 'span', 'div', 'href', 'src', 'id', 'value',
                'true', 'false', 'null', 'none', 'auto', 'flex', 'block', 'hidden', 'aria', 'label', 'role', 'top',
                'left', 'right', 'center', 'solid', 'px', 'rem', 'em', 'rgba', 'var', 'transform', 'translate', 'lang'}


VOCAB = _vocab()


def is_text(visible):
    s = re.sub(r'&[a-z#0-9]+;', ' ', visible).strip()
    if not s or s in NOT_TEXT:
        return False
    if not re.search(r'\s', re.sub(r'\{\d+\}', '', s).strip()):
        # un seul mot : un vrai mot français (pas un identifiant, un chemin, une valeur technique, de l'allemand)
        w = re.sub(r'\{\d+\}', '', s).strip(' .…:!?')
        if not re.fullmatch(r"[A-Za-zàâçéèêëîïôûùÿœæÀÂÇÉÈÊËÎÏÔÛÙŒ'’]+", w) or w.isupper() and len(w) > 1:
            return False
    toks = WORD.findall(s)
    if not toks:
        return False
    fr = [w for w in toks if w.lower() in VOCAB or ACCENT.search(w)]
    if len(toks) == 1:
        return bool(fr) and bool(re.match(r'^[A-ZÀ-Ý]', s) or ACCENT.search(s))
    return len(fr) >= max(1, len(toks) / 2)


# ---------------------------------------------------------------- analyse lexicale

class Lexer:
    def __init__(self, src):
        self.s, self.i, self.prev = src, 0, ''
        self.strings, self.templates = [], []      # (début, fin) ; [(début, fin, parties)]

    def run(self):
        self.code(top=True)
        return self

    def code(self, top=False):
        s, depth = self.s, 0
        while self.i < len(s):
            c = s[self.i]
            if s.startswith('//', self.i):
                j = s.find('\n', self.i); self.i = len(s) if j < 0 else j; continue
            if s.startswith('/*', self.i):
                self.i = s.index('*/', self.i) + 2; continue
            if c in '\'"':
                st = self.i; self.i += 1
                while s[self.i] != c:
                    self.i += 2 if s[self.i] == '\\' else 1
                self.i += 1; self.strings.append((st, self.i)); self.prev = 'x'; continue
            if c == '`':
                self.template(); self.prev = 'x'; continue
            if c == '/':
                if self.prev in REGEX_PREV or self.prev in REGEX_KW:
                    self.regex(); self.prev = 'x'; continue
                self.i += 1; self.prev = '/'; continue
            if c == '{':
                depth += 1
            elif c == '}':
                if depth == 0 and not top:
                    return
                depth -= 1
            if c.isspace():
                self.i += 1; continue
            m = re.compile(r'[A-Za-z_$][\w$]*').match(s, self.i)
            if m:
                self.prev = m.group(0) if m.group(0) in REGEX_KW else 'x'; self.i = m.end(); continue
            m = re.compile(r'\d[\w.]*').match(s, self.i)
            if m:
                self.prev = 'x'; self.i = m.end(); continue
            self.prev = c if c not in ')]' else 'x'
            self.i += 1

    def regex(self):
        s = self.s; self.i += 1; cls = False
        while True:
            c = s[self.i]
            if c == '\\': self.i += 2; continue
            if c == '[': cls = True
            elif c == ']': cls = False
            elif c == '/' and not cls: break
            elif c == '\n': raise SyntaxError(f'expression régulière non fermée : {s[self.i-80:self.i]!r}')
            self.i += 1
        self.i += 1
        while self.i < len(s) and s[self.i].isalpha(): self.i += 1

    def template(self):
        s = self.s; start = self.i; self.i += 1; st = self.i; parts = []
        while True:
            c = s[self.i]
            if c == '\\': self.i += 2; continue
            if c == '`':
                parts.append(('txt', st, self.i)); self.i += 1
                self.templates.append((start, self.i, parts)); return
            if s.startswith('${', self.i):
                parts.append(('txt', st, self.i)); es = self.i; self.i += 2
                self.prev = '('; self.code(); self.i += 1
                parts.append(('expr', es, self.i)); st = self.i; continue
            self.i += 1


# ---------------------------------------------------------------- découpage en messages

TAG = re.compile(r'<(/?)([a-zA-Z][\w-]*)')


def items_of(js, parts):
    """Éléments d'un gabarit : ('txt', s, e) texte hors balise, ('tag', s, e, nom, bloc ?), ('expr', s, e),
    ('attr', nom, [('txt'|'expr', s, e)…]) valeur d'un attribut lisible."""
    flat = []
    for p in parts:
        if p[0] == 'expr':
            flat.append(('expr', p[1], p[2]))
        else:
            flat.extend(('ch', k, k + 1) for k in range(p[1], p[2]))
    out, i = [], 0
    while i < len(flat):
        kind, s, e = flat[i]
        if kind == 'ch' and js[s] == '<' and i + 1 < len(flat) and flat[i + 1][0] == 'ch' \
                and re.match(r'[a-zA-Z/]', js[flat[i + 1][1]]):
            m = TAG.match(js, s)
            name = (m.group(2) if m else '').lower()
            j, quote, cur, vals, attrs = i, None, None, [], []
            while j < len(flat):
                k2, s2, e2 = flat[j]
                ch = js[s2] if k2 == 'ch' else None
                if quote:
                    if ch == quote:
                        if cur:
                            attrs.append(('attr', cur, vals))
                        quote, cur, vals = None, None, []
                    elif cur:
                        if k2 == 'expr':
                            vals.append(('expr', s2, e2))
                        elif vals and vals[-1][0] == 'txt' and vals[-1][2] == s2:
                            vals[-1] = ('txt', vals[-1][1], e2)
                        else:
                            vals.append(('txt', s2, e2))
                elif ch in ('"', "'"):
                    quote = ch
                    am = re.search(r'([\w-]+)=$', js[max(0, s2 - 30):s2])
                    cur = am.group(1).lower() if am and am.group(1).lower() in READABLE_ATTR else None
                elif ch == '>':
                    break
                j += 1
            out.append(('tag', s, flat[min(j, len(flat) - 1)][2], name, name not in INLINE))
            out.extend(attrs)
            i = j + 1; continue
        if kind == 'expr':
            out.append(('expr', s, e))
        elif out and out[-1][0] == 'txt' and out[-1][2] == s:
            out[-1] = ('txt', out[-1][1], e)
        else:
            out.append(('txt', s, e))
        i += 1
    return out


def segments(js, items):
    """Messages : suites de texte, balises de mise en forme et expressions, entre deux balises de bloc ;
    plus les valeurs d'attributs lisibles."""
    segs, cur = [], []

    def flush():
        nonlocal cur
        while cur and cur[0][0] == 'txt' and not js[cur[0][1]:cur[0][2]].strip():
            cur.pop(0)
        while cur and cur[-1][0] == 'txt' and not js[cur[-1][1]:cur[-1][2]].strip():
            cur.pop()
        if cur:
            segs.append(cur)
        cur = []
    for it in items:
        if it[0] == 'tag':
            if it[4]: flush()
            else: cur.append(it)
        elif it[0] != 'attr':
            cur.append(it)
    flush()
    out = []
    for seg in segs:
        s0, e0 = seg[0][1], seg[-1][2]
        if seg[0][0] == 'txt':
            t = js[seg[0][1]:seg[0][2]]; s0 = seg[0][1] + len(t) - len(t.lstrip())
        if seg[-1][0] == 'txt':
            e0 = seg[-1][1] + len(js[seg[-1][1]:seg[-1][2]].rstrip())
        out.append((s0, e0, seg))
    for it in items:
        if it[0] == 'attr' and it[2]:
            out.append((it[2][0][1], it[2][-1][2], it[2]))
    return out


def visible_text(js, seg):
    t = ''.join(js[x[1]:x[2]] for x in seg if x[0] == 'txt')
    return re.sub(r'<[^>]*>', ' ', t)


def slug(text):
    t = unicodedata.normalize('NFD', re.sub(r'<[^>]*>|\{\d+\}|&[a-z]+;', ' ', text))
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn').lower()
    return '_'.join(re.findall(r'[a-z0-9]+', t)[:5]) or 'txt'


# ---------------------------------------------------------------- remplacement

def main():
    dry = '--dry' in sys.argv
    path = os.path.join(ROOT, 'index.html')
    html = open(path, encoding='utf-8').read()
    a = html.index('<script>') + len('<script>'); b = html.index('</script>', a)
    js = html[a:b]
    skip = [(m.start(), m.end()) for m in re.finditer(r'/\* (?:LANG_DATA|USER_DATA|I18N_DATA):BEGIN.*?:END \*/', js, re.S)]
    for f in SKIP_FUNCS:
        st = js.index('function ' + f + '(')
        nx = re.search(r'\n(?:async )?function |\nconst |\nlet ', js[st + 10:])
        skip.append((st, st + 10 + nx.start()))
    funcs = [(m.start(), m.group(1) or m.group(2)) for m in
             re.finditer(r'(?:function\s+([A-Za-z_$][\w$]{3,})|(?:const|let)\s+([A-Za-z_$][\w$]{3,})\s*=)', js)]

    def owner(pos):
        o = 'app'
        for p, n in funcs:
            if p > pos: break
            o = n
        return o

    lx = Lexer(js).run()
    edits = []
    for st, en in lx.strings:
        if any(x <= st < y for x, y in skip):
            continue
        body = js[st + 1:en - 1]
        if re.search(r'[<>{}`]|="', body):
            continue
        before = js[max(0, st - 12):st].rstrip(); after = js[en:en + 3].lstrip()
        if after.startswith(':') and (before.endswith(('{', ',')) or re.search(r'\bcase$', before)):
            continue          # clé d'objet ou étiquette de « case » : jamais remplacée
        forced = owner(st) in FORCE_CONSTS and re.fullmatch(r"[a-zàâçéèêëîïôûùÿœæ ,/'-]+", body)
        if forced or is_text(body):
            edits.append(dict(s=st, e=en, kind='str', raw=js[st:en], args=[]))
    for st, en, parts in lx.templates:
        if any(x <= st < y for x, y in skip):
            continue
        for s0, e0, seg in segments(js, items_of(js, parts)):
            if not is_text(visible_text(js, seg)):
                continue
            pieces, args, pos, ok = [], [], s0, True
            for x in [x for x in seg if x[0] == 'expr'] + [None]:
                upto = x[1] if x else e0
                txt = js[pos:upto]
                if re.search(r'[{}]|\$\{|\\u', txt):
                    ok = False
                pieces.append(txt)
                if x:
                    pieces.append('{%d}' % len(args)); args.append((x[1] + 2, x[2] - 1)); pos = x[2]
            if ok:
                edits.append(dict(s=s0, e=e0, kind='msg', raw='`' + ''.join(pieces) + '`', args=args))
    edits.sort(key=lambda d: (d['s'], -d['e']))
    # complète le fichier existant : mêmes clés pour les mêmes textes, nouveaux noms sans collision
    old_path = os.path.join(ROOT, 'i18n', 'fr.json')
    old = json.load(open(old_path, encoding='utf-8')) if os.path.exists(old_path) else {}
    fr, ctx, used = {}, [], set(old)
    by_val = {v: k for k, v in old.items() if v is not None}
    for d in edits:
        v = d['raw'][1:-1] if '\\' not in d['raw'] else None
        if v is not None and v in by_val:
            d['key'] = by_val[v]; continue
        base = owner(d['s']) + '.' + slug(d['raw'][1:-1])
        k, n = base, 2
        while k in used:
            k = f'{base}_{n}'; n += 1
        used.add(k); d['key'] = k; fr[k] = v
        if v is not None: by_val[v] = k
        ctx.append((k, d['raw'][1:-1], js[max(0, d['s'] - 80):d['e'] + 40].replace('\n', ' ').replace('\t', ' ')))

    def render(s, e):
        out, pos = [], s
        for d in edits:
            if d['s'] < pos or not (s <= d['s'] and d['e'] <= e):
                continue
            out.append(js[pos:d['s']])
            if d['kind'] == 'str':
                out.append(f"T('{d['key']}')")
            else:
                args = ','.join(render(x, y) for x, y in d['args'])
                out.append("${T('" + d['key'] + "'" + (f',[{args}]' if d['args'] else '') + ')}')
            pos = d['e']
        out.append(js[pos:e])
        return ''.join(out)

    new = render(0, len(js))
    print(f"{len(edits)} textes remplacés ({sum(d['kind']=='msg' for d in edits)} messages de gabarit), {len(fr)} clés")
    json.dump([(d['key'], d['raw']) for d in edits], open(os.environ.get('I18N_PROOF', '/tmp/i18n_proof.json'), 'w',
              encoding='utf-8'), ensure_ascii=False)
    if dry:
        for k, v, c in ctx[:int(os.environ.get('N', 60))]:
            print(f'{k} = {v!r}')
        return
    os.makedirs(os.path.join(ROOT, 'i18n'), exist_ok=True)
    json.dump({**old, **fr}, open(old_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cpath = os.path.join(ROOT, 'i18n', 'contexte.tsv')
    new_file = not os.path.exists(cpath)
    with open(cpath, 'a', encoding='utf-8') as f:
        if new_file: f.write('clé\tmessage\tcode\n')
        for k, v, c in ctx:
            f.write(f'{k}\t{v}\t{c}\n'.replace('\r', ' '))
    open(path, 'w', encoding='utf-8').write(html[:a] + new + html[b:])


if __name__ == '__main__':
    main()
