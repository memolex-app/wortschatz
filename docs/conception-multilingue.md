# Memolex multilingue : conception

État : **étapes 1, 2 et 3 faites** (12/11/2026) ; dette qualité de l'allemand soldée (versions 1.8.2 à 1.8.5). Ce document est la référence ; il est mis à jour à chaque étape.

## Objectif

5 langues (français, anglais, espagnol, allemand, italien), chacune apprenable depuis chacune des autres : 20 paires. Une seule appli, interface traduite dans les 5 langues. On avance par étapes, chacune avec un critère de réussite vérifiable, sans jamais dégrader ce qui est en ligne.

## Principe

Aujourd'hui, une paire = un jeu complet de fichiers (`lists-de-fr.json`…), et tout est mélangé : le mot allemand, sa traduction française, le chunk allemand et sa traduction.

Demain, on sépare ce qui appartient à **la langue apprise** de ce qui appartient à **la paire** :

| Appartient à la langue apprise (une fois) | Appartient à la paire (une fois par langue d'utilisateur) |
|---|---|
| le mot, son article, son pluriel, sa nature, son niveau | la traduction de chaque sens, avec ses nuances |
| ses sens (identifiants stables) | la traduction du chunk |
| le chunk (« *innerhalb* einer Woche ») | la traduction de chaque phrase, l'étiquette du sens illustré |
| les phrases d'exemple | |

Ajouter l'anglais comme langue d'utilisateur de l'allemand = traduire les sens, les chunks et les phrases. Les listes, les chunks allemands, les phrases et toutes les décisions sur l'allemand (articles, pluriels, mots retirés) sont repris tels quels.

## Le format source (`data/`)

Fichiers texte à tabulations (TSV), une ligne par élément, éditables à la main et lisibles dans un diff git. **C'est la seule référence à modifier.** Les JSON lus par l'appli en sont générés et ne s'éditent plus directement.

```
data/de/lexemes.tsv        key · level · pos · art · lemma · plural · extra
data/de/senses.tsv         sense · key
data/de/chunks.tsv         key · chunk
data/de/examples.tsv       id · key · sentence · highlight · origin
data/de-fr/glosses.tsv     sense · gloss
data/de-fr/cards.tsv       key · translation        (traduction libre d'une carte, rare)
data/de-fr/chunks.tsv      key · translation
data/de-fr/examples.tsv    id · translation · sense_label
```

Règles :
- **Clé d'un mot** = article + mot (« das Gericht », « essen », « l'amico »). C'est déjà la règle d'unicité de la procédure de contrôle.
- **Identifiant d'un sens** = clé + `#n` (« das Gericht#2 »). Il ne change jamais. Pour découper un sens trop large, on crée `#2a` et `#2b` et on garde `#2` comme ancien nom : les traductions déjà relues ne sont pas cassées.
- **Ordre des lignes** de `lexemes.tsv` = ordre de fréquence dans chaque niveau, c'est-à-dire l'ordre des paquets.
- `~` = champ absent (différent d'un champ vide). Sert à reproduire les fichiers historiques à l'identique.
- `extra` : 7ᵉ colonne historique (genre italien quand l'article est élidé : *l'amico* → m).
- `cards.tsv` : seulement quand la traduction d'une carte ne se recompose pas à partir des sens (2 cartes allemandes : *los*, *setzen*, qui contiennent une expression « = »).
- Une phrase ou un chunk non traduit dans une paire n'est pas publié pour cette paire (jamais de phrase sans traduction).

## Outils (`tools/`)

- `migrate.py L U` : conversion unique JSON publiés → `data/`. Fait pour de-fr et it-fr. **Ne plus le relancer** : il écraserait les corrections faites dans `data/`.
- `build.py L U` : `data/` → `lists-`, `chunks-`, `examples-L-U.json`.
- `build.py L U --check` : compare au fichier publié sans rien écrire.

## Étape 1 : format source, sans rien changer en ligne (faite, 11/11/2026)

Critère : régénérer les fichiers publiés **à l'octet près**. Résultat : 6/6 fichiers identiques (de-fr et it-fr). Les empreintes allemandes sont celles de la référence `ref-fr-de-2026-11-11`.

| Paire | Mots | Sens | Chunks | Phrases |
|---|---|---|---|---|
| de-fr | 7 777 | 10 030 | 7 777 | 6 327 |
| it-fr | 8 180 | 8 851 | 8 180 | 4 435 |

**À partir de maintenant, toute correction des listes allemandes ou italiennes se fait dans `data/`, puis `build.py`.**

## Contrôles (`tools/check.py L U [--full] [--compare]`)

- Généraux pour une langue d'utilisateur française : `check_dups` (doublons, cartes ambiguës), `chunks_check`, `register`, `ex_gloss` (avec `--full`).
- Par langue apprise : `plural_check` (it, alertes « à vérifier » informatives), `ex_pos` (it, `--full`), `prep_case` (de, audit n° 9).
- Par paire : `faux_amis` (catalogues it-fr et de-fr ; de-fr commencé le 11/11/2026, entrées sûres seulement).
- Dépendances : `snowballstemmer`, spaCy avec `fr_core_news_md`, `it_core_news_lg` (et `de_core_news_md` pour un futur `ex_pos` allemand).
- Une nouvelle paire doit avoir ses contrôles **dans la langue de l'utilisateur** (articles, registre, racines) : ceux d'aujourd'hui sont écrits pour le français.

### Premier passage des contrôles sur l'allemand (11/11/2026)
Ces contrôles n'avaient jamais tourné sur les données allemandes publiées. Résultats, **non corrigés** (décisions d'Andrea à prendre) :
- `check_dups` : 0 doublon, **214 cartes ambiguës** (carte sans nuance dont la traduction est incluse dans celle d'un autre mot de même nature : *auch* « aussi » ⊂ *drum* « aussi (familier…) », *der Teil* « la partie » ⊂ *die Partie* « la partie (de jeu…) »). Retard attendu depuis la simplification d'octobre (le contrôle des inclusions n'avait pas été refait).
- `register` : 14 cartes à mot familier ou vulgaire sans étiquette (*bosser*, *gosse*, *boulot*, *merde*, *fils de pute*, *putain*, *clope*… ; *chouette* (l'oiseau) et *truc* (tour) sont de fausses alertes).
- `chunks_check` : 3 chunks de 4 mots en A1–A2, tous des conjonctions doubles (*nicht heute, sondern morgen*, *zwar teuer, aber gut*, *weder heute noch morgen*) : tolérance à décider.
- `prep_case` : *versus* absent de la table des cas.
- `faux_amis` : 0.
- `ex_gloss` : 783 alertes sur 6 123 phrases, surtout des traductions libres justes (« noch » → « toujours »), mais aussi de vraies erreurs : *der Laut* illustré par « Tom spielt Laute » (*die Laute* = le luth), *der Teil* par « Teilen macht Freude » (verbe), une phrase allemande fautive (« Laut Tageszeitung gab in der Stadt einen Brand », sans *es*). Relecture à faire, en commençant par les noms ; un `ex_pos` allemand attraperait les verbes pris pour des noms.

## Corrections des données (décisions)

- Une correction = une ligne dans un fichier daté `data/<L>-<U>/decisions/AAAA-MM-JJ-<nom>.tsv` (clé · nouvelle traduction · justification), appliqué par `tools/apply_decisions.py`, puis `build.py` et `check.py`.
- Avant application : essai, comparaison des ambiguïtés avant / après (aucune nouvelle), liste montrée à Andrea.
- **Lot 1 (11/11/2026, version 1.8.2)** : `2026-11-11-ambig-1.tsv`, 50 cartes (13 registre, 37 ambiguïtés). Cartes ambiguës 214 → 179, 0 doublon, 0 mot familier sans étiquette (reste *chouette*, fausse alerte).
- **Lot 2 (11/11/2026, version 1.8.3)** : `2026-11-11-ambig-2.tsv`, 44 cartes. Ambiguïtés 179 → 137 (dont *der Arzt*, exception vérifiée dans `tools/ignore_check_dups_de-fr.txt`), 0 nouvelle, 0 doublon.
- Leçon (correction d'Andrea sur *erwarten*) : lever une ambiguïté ne doit jamais retirer le **sens principal** d'un mot. Si les deux mots partagent un sens courant, on distingue par une nuance sur chacun (*warten* « attendre (patienter) » / *erwarten* « attendre (une visite, un événement prévu), s'attendre à »), on ne supprime pas. Vérifier chaque retrait de sens contre le Duden (sens n° 1).
- **Lot 3 (12/11/2026, version 1.8.4)** : `2026-11-12-ambig-3.tsv`, 137 cartes, rédigé par Claude sur délégation d'Andrea (pas de relecture ligne à ligne). Méthode prudente : nuance ajoutée sur la carte signalée, aucun sens retiré nulle part. Ambiguïtés 137 → **0**, 0 doublon. Nuances vérifiées automatiquement (ni mot appris, ni terme de grammaire, ni « = » / « + ») sur les trois lots.
- Contrôles ajustés le même jour : exceptions vérifiées `tools/ignore_register_de-fr.txt` (*die Eule* « chouette », l'oiseau) ; `chunks_check` accorde un mot de plus aux conjonctions doubles (*weder … noch*, *zwar … aber*, *nicht … sondern*).
- Reste : *versus* absent de la table des cas (cas à vérifier dans le Duden, modification de l'appli) ; relecture des phrases d'exemple (783 alertes).
- **Phrases d'exemple (12/11/2026, version 1.8.5)**, sur délégation d'Andrea : 830 alertes relues une à une (783 `ex_gloss` + 52 du nouveau `ex_form_de`, 5 en commun). `data/de/decisions/2026-11-12-phrases.tsv` : **39 phrases retirées** (autre mot : *Laute* « luth », *die Marsch* « marais », *selben*, *teilen* ; verbe à particule : *denkt … nach*, *spricht … aus* ; nom de langue pour une carte adjectif : *Englisch*, *Russisch*… ; allemand fautif ; traduction fausse ; 1 phrase à contenu sexuel explicite, sous deux cartes) et **3 corrigées** (*muß* → *muss*, surlignage recalculé). 6 327 → 6 288 phrases ; 30 cartes n'ont plus de phrase (règle : mieux qu'un faux sens ; elles gardent leur chunk). Les 764 + 42 phrases gardées sont des exceptions vérifiées (`tools/ignore_ex_gloss_de-fr.txt`, `tools/ignore_ex_form_de_de-fr.txt`).
- Nouveaux outils : `tools/ex_form_de.py` (forme surlignée : majuscule, nature, lemme ; dans `check.py --full` pour l'allemand) ; `tools/apply_ex_decisions.py` (retire ou corrige une phrase de la langue apprise, pour toutes les paires). Exceptions des contrôles de phrases désormais par paire (`ignore_<outil>_<paire>.txt`).
- Balayage de toutes les phrases (pas seulement les alertes) : contenu sexuel et ancienne orthographe (*muß*, *daß*…). À refaire à chaque nouvelle langue, avec les mots de cette langue.
- *versus* : cas non trouvé dans une source fiable, laissé hors de la table des cas (seule alerte restante).
- Règle validée par Andrea (11/11/2026) : pour de vrais synonymes, le mot de base peut porter « (courant) » quand ses synonymes plus rares sont tous marqués (soutenu, familier…) ; ce n'est pas l'étiquette vide « terme courant » retirée en octobre.

## Étape 3 : numéros Tatoeba et crédits (faite, 12/11/2026, version 1.8.6)

- `tools/tatoeba_link.py L U <exports>` : ajoute `tatoeba` (numéro) et `author` à `data/<L>/examples.tsv` (phrase) et `data/<L>-<U>/examples.tsv` (traduction). Choix entre doublons Tatoeba : paire citée dans les anciens crédits, puis paire liée sur Tatoeba, puis numéro le plus ancien. Exports : https://downloads.tatoeba.org/exports/per_language/ (`<l3>_sentences_detailed.tsv`, `<l3>-<u3>_links.tsv`), téléchargés hors du dépôt.
- Exception : `data/<L>/tatoeba_manual.tsv` (phrase gardée dans une version différente de Tatoeba : *Sie hört Podcasts, um …* ; Tatoeba a depuis écrit « hört Podcasts zu », moins correct).
- 3 traductions fautives corrigées d'après la version actuelle de Tatoeba (*Elle dors* → *dort*, *réagit* → *réagi*, accord) : `data/de-fr/decisions/2026-11-12-traductions-phrases.tsv`.
- `build.py` génère désormais `credits-L-U.json` (une ligne par paire publiée, triée par numéro de phrase). de-fr : 6 129 → 5 728 paires, 569 → 550 contributeurs ; it-fr : 4 320 → 4 307. Aucune paire ni aucun auteur nouveau : seules disparaissent les phrases qui ne sont plus publiées.
- Les outils de décisions conservent désormais toutes les colonnes des fichiers (`write_rows`).

### Couverture Tatoeba pour les futures langues d'utilisateur (12/11/2026)
Phrases de Memolex qui ont une traduction **directe** sur Tatoeba (sans passer par une autre langue) :

| Langue apprise → langue de l'utilisateur | Phrases traduites | Cartes qui gardent au moins une phrase |
|---|---|---|
| allemand → anglais | 61 % | 64 % |
| allemand → espagnol | 23 % | 25 % |
| allemand → italien | 7 % | 8 % |
| italien → anglais | 52 % | 52 % |
| italien → espagnol | 7 % | 7 % |
| italien → allemand | 11 % | 12 % |

**Conséquence et choix retenu (12/11/2026, question d'Andrea : « ces exemples ne sont pas traduisibles ? »)** : on garde les mêmes phrases dans toutes les paires (elles ont été relues et corrigées ; changer de phrases obligerait à refaire ce travail par paire). Pour chaque nouvelle paire :
1. traduction Tatoeba **directe** quand elle existe (humaine, souvent native) ;
2. sinon, traduction rédigée pour Memolex **à partir de la phrase de la langue apprise**, jamais à partir d'une autre traduction (pas de pivot), marquée `mx` au niveau de la paire ;
3. mêmes contrôles (`ex_gloss` dans la langue de l'utilisateur) et même seuil (échantillon relu ≥ 95 % juste). Relecteur : Andrea pour l'italien ; à trouver pour l'espagnol.
Licence : CC BY 2.0 FR autorise la traduction avec attribution ; crédit « phrase : auteur Tatoeba · traduction : Memolex ».
Adaptation technique à faire : origine de la traduction au niveau de la paire (`data/<L>-<U>/examples.tsv`), crédits en conséquence.
**Chunks** (rappel d'Andrea, 12/11/2026) : ils ont été rédigés pour Memolex, ils n'ont pas de source extérieure. Le chunk de la langue apprise (`data/<L>/chunks.tsv`) est le même pour toutes les paires ; chaque paire reçoit sa traduction rédigée depuis ce chunk (`data/<L>-<U>/chunks.tsv`), avec les règles du § 2 bis de la procédure (traduction naturelle, registre conservé).
**Relecture** (décision d'Andrea, 12/11/2026) : on rédige d'abord ; les corrections se font **après, par échantillon**, avec les contrôles automatiques à chaque étape.
Volume pour l'allemand : ~2 200 traductions à rédiger vers l'anglais, ~4 400 vers l'espagnol, ~5 300 vers l'italien.

## Limites connues (à traiter dans les étapes suivantes)

1. **Sens initialisés depuis le français.** Un sens = une traduction française de la carte. Parfois ce sont vraiment deux sens (*Erleichterung* : le soulagement / l'allègement), parfois deux traductions du même sens (*sicher* : sûr / certain ; *in* : dans / en). Avant d'ajouter l'anglais, il faut relire les 2 239 mots allemands à plusieurs sens et fusionner les faux doubles (le sens fusionné garde ses deux traductions françaises).
2. ~~Phrases sans numéro Tatoeba~~ : réglé à l'étape 3 (les identifiants internes `clé@n` restent, le numéro Tatoeba est une colonne).
3. **Non migré** : le dictionnaire (`dict-de-fr.json`, 46 029 mots, importé d'une source externe). Il reste tel quel pour l'instant.
4. **Grammaire écrite dans l'appli** : `LANGS`, `ART_RE`, `PREP_CASE`, couleurs de genre, tout cela est dans `index.html` et pensé pour de/it. À déplacer dans un fichier de description par langue (`data/<L>/langue.json` : genres, articles, élision, cas, ce qu'on fait deviner).
5. **Interface entièrement en français** : tous les textes de l'appli sont écrits en dur. À extraire dans des fichiers de traduction de l'interface.
6. **Langue de l'utilisateur fixée au français** dans l'appli (`dataFile = k-LANG-fr.json`, article français, comparaisons « le / la / l' »).

## Feuille de route

Chaque étape a son critère de sortie. Rien n'est publié tant qu'il n'est pas atteint.

| # | Étape | Critère de sortie |
|---|---|---|
| 1 | Format source + build à l'identique | ✅ 6/6 fichiers identiques |
| 2 | Contrôles sur le format source, par paire (`tools/check.py`) | ✅ sorties identiques sur `data/` et sur les JSON (de-fr, it-fr, contrôles rapides et complets) |
| 3 | Numéros Tatoeba retrouvés pour chaque phrase, crédits générés | ✅ 100 % (de-fr 5 821, it-fr 4 435) ; crédits générés : toutes les paires et tous les auteurs déjà présents dans les anciens crédits, les phrases retirées n'y figurent plus |
| 4 | Grammaire par langue sortie de l'appli (`langue.json`) | appli de/it inchangée à l'usage (tests Playwright) |
| 5 | Appli : langue de l'utilisateur variable (`L-U`), interface traduisible | appli en français inchangée ; textes extraits |
| 6 | Relecture des sens allemands (fusion des faux doubles) | chaque mot à plusieurs sens relu ; build de-fr toujours identique en contenu |
| 7 | Première nouvelle paire : français → anglais ou espagnol (nouvelle liste) | échantillon de 300 cartes ≥ 95 % juste ; contrôles à 0 |
| 8 | Première nouvelle langue d'utilisateur : anglais → allemand (traduction des sens) | idem |
| … | Une paire à la fois | idem |

## Règles de qualité (rappel)

- Jamais de traduction automatique en passant par le français : chaque paire est rédigée et contrôlée pour elle-même.
- Les nuances, les faux amis, les doublons et les ambiguïtés se contrôlent **par paire** : deux mots allemands distincts en français peuvent se confondre en anglais.
- Seuil de publication par paire : échantillon relu ≥ 95 % de traductions justes ; contrôles automatiques à 0.
- Tout commiter et pousser à la fin de chaque session de travail.
