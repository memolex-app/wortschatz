"""Contrôle 3 : faux amis italien-français.
Catalogue de départ (à enrichir) : mot italien -> traductions françaises trompeuses (ressemblance de forme, sens différent).
Une carte est signalée si l'une de ses traductions est un faux ami du catalogue. Le catalogue est volontairement court
(entrées sûres seulement) : l'enrichir à chaque erreur trouvée par un relecteur.
Usage : python3 faux_amis.py
"""
import sys, re, unicodedata
from common import load, shown, fr_senses
# (mot italien, nature ou '*', traduction française trompeuse, sens réel / remarque)
FAUX_AMIS = [
 ('puntualmente', '*', 'ponctuellement', "= comme prévu / sans faute ; « ponctuellement » signifie surtout « de façon occasionnelle »"),
 ('camera', 'n', 'caméra', 'camera = chambre ; caméra = telecamera'),
 ('cantina', 'n', 'cantine', 'cantina = cave ; cantine = mensa'),
 ('magazzino', 'n', 'magasin', 'magazzino = entrepôt ; magasin = negozio'),
 ('morbido', 'adj', 'morbide', 'morbido = doux, moelleux'),
 ('pretendere', 'v', 'prétendre', 'pretendere = exiger ; prétendre = sostenere'),
 ('svelto', 'adj', 'svelte', 'svelto = rapide, vif ; svelte = snello'),
 ('bravo', 'adj', 'brave', 'bravo = doué, compétent ; brave = coraggioso'),
 ('brutto', 'adj', 'brut', 'brutto = laid, mauvais ; brut = grezzo'),
 ('parenti', 'n', 'parents', 'parenti = famille proche, proches ; parents = genitori'),
 ('educato', 'adj', 'éduqué', 'educato = poli ; éduqué = istruito'),
 ('sufficienza', 'n', 'suffisance', 'sufficienza = niveau suffisant, note de passage ; suffisance = presunzione'),
 ('convenienza', 'n', 'convenance', 'convenienza = avantage, intérêt ; convenance = decoro'),
 ('pinguino', 'n', 'pingouin', 'pinguino = manchot ; pingouin = uccello artico (alca)'),
 ('compravendita', 'n', 'compravente', 'mot inexistant en français'),
 ('cuffia', 'n', 'écouteurs', 'cuffia = casque audio ; écouteurs = auricolari'),
 ('sussidio', 'n', 'subside', 'sussidio = allocation ; subside = vieilli'),
 ('collegio', 'n', 'collège', 'collegio = pensionnat, collège électoral ; collège = scuola media'),
 ('caramella', 'n', 'caramel', 'caramella = bonbon ; caramel = caramello'),
 ('mancia', 'n', 'manche', 'mancia = pourboire ; manche = manica'),
 ('stampa', 'n', 'estampe', 'stampa = presse, impression'),
 ('fiera', 'n', 'fière', 'fiera = foire, salon'),
 ('mobile', 'n', 'mobile', 'il mobile = meuble'),
]
def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
def run(repo='..'):
    cards, _, _ = load(repo)
    hits = []
    for c in cards:
        gl = [norm(g) for g in fr_senses(c['fr'])]
        for w, nat, bad, note in FAUX_AMIS:
            if c['w'] == w and (nat == '*' or c['nat'].startswith(nat)) and norm(bad) in gl:
                hits.append((c, bad, note))
    return hits
if __name__ == '__main__':
    for c, bad, note in run():
        print(f"{c['i']}|{c['lv']}|{shown(c)} = {c['fr']} | faux ami « {bad} » : {note}")
