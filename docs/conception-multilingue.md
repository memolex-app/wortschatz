# Memolex multilingue : conception

État : **étapes 1 à 4 faites** (12/11/2026) ; dette qualité de l'allemand soldée (versions 1.8.2 à 1.8.5). Ce document est la référence ; il est mis à jour à chaque étape.

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

## Étape 4 : grammaire de chaque langue hors du code (faite, 12/11/2026, version 1.8.7)

- **`data/<L>/langue.json`** décrit la langue apprise. Il contient :
  - les noms et formes utilisés par l'interface (`name`, `adj`…) et les lettres spéciales ;
  - la voix (`tts.tag`, `tts.rate`) ;
  - les **articles** (`a`, genre `g` m/f/n ou vide, `pl` pour un article du pluriel, `elided` pour un article élidé collé au mot), dans l'ordre des boutons du quiz ;
  - le style du **pluriel** : `suffix` (allemand : « -e », affiché « die Hunde ») ou `full` (italien : écrit en entier avec son article), avec `pluralArticle` ;
  - `storeGender` (genre enregistré sur la carte quand l'article ne le dit pas : *l'amico*), `dictArticle` (article des entrées du dictionnaire : déduit du genre ou donné par l'entrée), `searchFolds` (recherche tolérante : *ae* → *ä*), `artOptions` (menu « Article » du formulaire), `legend` (code couleur de la liste) ;
  - les **cas** (`cases` : noms proposés au quiz, cas de chaque préposition, notes des prépositions mixtes, verbes à préposition), seulement pour une langue à cas.
- **`tools/build_app.py`** injecte ces descriptions dans `index.html` entre les balises `LANG_DATA:BEGIN/END` (l'appli démarre sans chargement supplémentaire) ; `--check` vérifie que l'appli est à jour. **Ne jamais éditer ce bloc à la main.**
- Le code ne teste plus « allemand » ou « italien » pour la grammaire : il lit `LG(langue)`. Exceptions voulues : l'identité historique des cartes allemandes (`keyOf`, `langOf` par défaut `de`), à garder pour ne pas casser les données des utilisateurs.
- **`tools/regress_app.py capture|compare`** : test de non-régression. Pour chaque mot des listes (de et it) : couleur, mot affiché, ligne de grammaire, cas, quiz ; analyse de mots tapés et de lignes collées ; verdicts du quiz des cas ; dictionnaire ; recto et verso d'un échantillon de cartes dans les deux sens ; écrans Mots, Ajouter, Guide, Statistiques, choix de la langue, recherche ; voix ; ajout d'un mot tapé à la main. Horloge et hasard figés. Référence capturée sur la 1.8.6, comparée à la 1.8.7 : **0 différence**, 0 erreur JavaScript. À relancer avant chaque modification de l'appli.
- Ajouter une langue apprise = écrire son `langue.json`. Points à prévoir au moment voulu : une langue **sans article ni genre** (anglais : `articles: []`, pas de quiz d'article ni de couleur), une langue à **trois genres et cas** autre que l'allemand (russe : le quiz des cas porte aujourd'hui sur les prépositions), une écriture **de droite à gauche** (étape 5).

## Étape 5 : langue de l'utilisateur et interface (en cours)

Découpage : 5.1 langue de l'utilisateur variable ; 5.2 textes courts de l'interface dans un fichier de traduction ; 5.3 guide ; 5.4 traductions (en, es, it, de) et choix de la langue de l'utilisateur. Chaque morceau : test de non-régression à 0 différence en français.

### 5.1 (faite, 12/11/2026, version 1.8.8)
- **`data/<U>/utilisateur.json`** décrit la langue de l'utilisateur : nom et code (« Français », « FR »), `locale` (dates, nombres, tri : `fr-FR`), `dir` (sens de l'écriture), **articles** classés par nature (`def`, `indef`, `part`) et articles élidés (`l`), `gramNoteWords` (mots qui signalent une note grammaticale, envoyée au verso).
- Les articles à ignorer dépendent de l'usage, comme avant : tri par la traduction = toutes les natures ; comparaison des traductions (doublons, cartes ambiguës) = définis et indéfinis ; recherche dans le dictionnaire = définis.
- `build_app.py` injecte aussi ces descriptions (bloc `USER_DATA`).
- Dans l'appli : variable `UL` (langue de l'utilisateur, `localStorage` `mx-ul`, défaut `fr`) ; fichiers `<type>-<langue apprise>-<UL>.json` ; une carte porte `ul` seulement si elle n'est pas en français (`ulOf` : absent = `fr`, toutes les cartes existantes) ; le paquet de mots ne montre que les cartes de la paire choisie ; identité d'une carte préfixée par la langue de l'utilisateur sauf pour le français (`keyOf` : les clés existantes ne changent pas).
- Test de non-régression étendu (tri par la traduction et par le mot, clés de comparaison, doublons à l'ajout) : 1.8.7 → 1.8.8, **0 différence**.
- Restent à adapter pour une autre langue d'utilisateur : les contrôles Python (`tools/*.py`, écrits pour le français : articles, registre, racines Snowball, spaCy fr).

### 5.2 (faite, 12/11/2026, version 1.8.9)
- **`i18n/<langue>.json`** : textes de l'interface, clé → message. `i18n/fr.json` : 416 clés (hors guide). `i18n/contexte.tsv` : extrait du code autour de chaque clé, pour les traducteurs.
- Dans l'appli : `T('clé')` ou `T('clé', [valeurs])` (remplace `{0}`, `{1}`… dans l'ordre). Langue de l'interface = `mx-ul` ; une clé absente d'une langue retombe sur le français. Le cadre fixe de la page (en-tête, compteurs, onglets) porte des attributs `data-t` / `data-ta`, remplis au démarrage ; la page reçoit `lang` et `dir` de la langue de l'utilisateur. `build_app.py` injecte toutes les langues de `i18n/` (bloc `I18N_DATA`).
- Messages = **phrases entières** avec leurs balises de mise en forme (`<b>`, `<i>`, `<span>`…) et des emplacements `{n}` pour les valeurs insérées ; découpage aux seules balises de bloc. Les noms de clés indiquent la fonction où le texte apparaît.
- Extraction : `tools/i18n_extract.py` (analyse lexicale du JavaScript ; une fois). Exclus volontairement : identifiants techniques (`POST`, `Content-Type`, chemins, `mx-…`, classes CSS), clés d'objet et étiquettes `case`, guide (5.3). 7 cas mixtes faits à la main.
- **Preuve d'équivalence** (`tools/i18n_proof.py`) : pour chaque texte remplacé, le navigateur évalue le code d'origine ; `T()` renvoie exactement la même chaîne (0 erreur sur 426 occurrences) — l'appli française est donc identique sur **tous** les écrans, y compris ceux que le test d'écrans ne rend pas. Test d'écrans : 1.8.8 → 1.8.9, **0 différence**. Essai avec une langue fictive : textes traduits remplacés, le reste retombe sur le français, données inchangées.
- **Pluriels** : ~40 pluriels « à la française » (`mot${n>1?'s':''}`) sont pour l'instant des valeurs insérées (`{1}` vaut « s » ou rien). À convertir en vrais pluriels au moment des traductions (5.4) : l'italien et l'espagnol ne forment pas leur pluriel avec « s ».
- Restent en français, hors de l'appli : textes des notifications envoyées par le serveur (`supabase/functions`), `sw.js`.

### 5.3 (faite, 12/11/2026, version 1.9.0)
- **Guide** extrait : 88 nouveaux messages (paragraphes entiers, avec liens et mise en forme). `i18n/fr.json` : 527 clés au total.
- Les 10 passages propres à une langue apprise (code couleur, quiz des articles, format d'une liste collée, lettres spéciales, dictionnaire, exemple de mot souligné, exemple « une phrase par sens », exemple de mots de même traduction, sources des listes, mots utiles peu fréquents) + l'exemple de nom lu avec son article sont des messages **`guide.<langue apprise>.<nom>`**. Une nouvelle langue apprise ajoute les siens ; le code n'a plus aucun test « allemand / italien ».
- `dictDefinitions` (description de la langue) : le dictionnaire contient des définitions dans la langue apprise (allemand : oui ; italien : non).
- Seule différence voulue avec la 1.8.9 : le guide italien donnait l'exemple allemand « die Geduld » pour la lecture du nom avec son article ; il donne maintenant « la pazienza ». Preuve : 95/95 ; test d'écrans : cette seule différence.

### 5.4, première partie (faite, 12/11/2026, version 1.9.1)
- **Pluriels** : `{0:one=mot|other=mots}` dans un message choisit la forme selon le nombre `{0}` et les règles de la langue (`Intl.PluralRules` : one, two, few, many, other). 40 pluriels « à la française » convertis (`tools/js/plural_convert.mjs`, analyse du code avec acorn, en plusieurs passes pour les messages imbriqués). Preuve (`tools/js/plural_proof.mjs`) : 23 messages × toutes les combinaisons de 0, 1, 2, 3, 7, 21, 100, 1 000 000 = 352 cas, 0 différence.
- **Quiz des cas** : noms des cas (`case.Akk`…) et verdicts complets par cas (« il fallait l’accusatif ») dans `i18n/` ; la description de l'allemand ne garde que les codes (`cases.codes`).
- **Libellés des langues apprises** (nom, adjectifs, légende, formats d'exemple, libellés du menu « Article ») : `i18n/<langue>.json`, clés `lang.<langue apprise>.<champ>` ; `LUI(l)` les fusionne avec la description. `langue.json` ne contient plus que de la grammaire et des exemples dans la langue apprise. `build_app.py` refuse une langue apprise sans ses libellés français. Les noms de langue des notes grammaticales sont tirés des adjectifs.
- Incident évité : la première conversion des pluriels a corrompu un message imbriqué ; détecté avant publication (code invalide), recommencé à partir de la sauvegarde avec un traitement en passes.
- Test d'écrans : seule différence avec la 1.8.9, « la pazienza » (voulue).

### 5.4, deuxième partie (faite, 12/11/2026, version 1.9.2)
- **Paires publiées** : `build_app.py` injecte la liste des `lists-<L>-<U>.json` présents (bloc `PAIRS`). Le choix de la langue apprise ne propose que les langues qui ont une paire avec la langue de l'utilisateur ; le choix **« Ta langue »** n'apparaît que s'il existe des paires pour plusieurs langues d'utilisateur (aujourd'hui : français seulement, donc invisible). Changer de langue d'utilisateur recharge l'appli (interface et données) ; la langue apprise est oubliée si la paire n'existe pas.
- `data/<U>/utilisateur.json` reçoit `selfFrom` (« le français » : « Depuis le français… »).
- **`tools/i18n_check.py`** : chaque traduction garde les mêmes emplacements `{n}`, les mêmes pluriels (avec une forme `other`), les mêmes balises et entités que le français ; clés inconnues refusées ; taux de traduction affiché. `build_app.py` refuse un fichier fautif.
- Correction : « 1 mots » après un changement de langue → pluriel.
- Essai de bout en bout avec une fausse paire allemand → anglais (retirée ensuite, appli identique) : choix « Ta langue » affiché, interface en anglais pour les textes traduits et en français pour les autres, données `lists-de-en.json`, italien masqué faute de paire.

### Reste de 5.4 : les traductions
- Recommandation : traduire l'interface d'une langue **au moment où sa première paire est prête** (étape 8 pour l'anglais) : les textes peuvent encore changer d'ici là, et une interface traduite sans données ne sert à personne. Volume par langue : ~565 messages (dont le guide et les libellés `lang.*`, `guide.<L>.*` pour chaque langue apprise disponible dans cette langue).
- À faire aussi pour une nouvelle langue d'utilisateur : `data/<U>/utilisateur.json` (articles, notes grammaticales, locale, `selfFrom`) ; contrôles Python (`tools/*.py`) adaptés à cette langue ; textes des notifications serveur (`supabase/functions`) et de `sw.js`.

## Étape 6 : sens de l'allemand (faite, 12/11/2026)

- Modèle : **un sens peut avoir plusieurs traductions** dans une langue d'utilisateur (`glosses.tsv` : plusieurs lignes pour le même identifiant de sens, dans l'ordre). `build.py` les joint dans l'ordre : la traduction affichée ne change pas.
- Relecture (sur délégation d'Andrea) des 2 222 mots allemands à plusieurs traductions françaises : **1 575 fusionnés** (traductions synonymes d'un même sens : *sicher* « sûr, certain », *das Jahr* « l'année, l'an », *bringen* « apporter, amener ») ; **645 gardés séparés** (vrais doubles sens : *die Bank* « le banc / la banque », *der Schimmel* « la moisissure / le cheval blanc », *hören* « entendre / écouter ») ; 2 mots à trois sens regroupés en partie (*anhalten* « arrêter, s'arrêter / durer », *aufhängen* « accrocher, étendre / raccrocher ») ; *los* et *setzen* (traduction libre) non touchés.
- Règle : **en cas de doute, garder séparé** (fusionner à tort ferait perdre une distinction dans une autre langue ; un faux double ne coûte qu'une traduction en double).
- Résultat : 10 030 → **8 436 sens** (7 130 mots à 1 sens, 635 à 2, 12 à 3). Fichiers publiés de-fr **identiques à l'octet** ; contrôles inchangés.
- Outil : `tools/apply_sense_merges.py` (fichier `data/de/decisions/2026-11-12-sens.tsv` : clé · groupes « 1+2 », « 1+2|3 » · motif ; idempotent). `apply_decisions.py` garde le regroupement quand une correction conserve le nombre de traductions (sinon : avertissement) et refuse un fichier qui n'a pas le format des décisions sur les cartes.
- Corrigé au passage : le fichier des 3 traductions de phrases (`phrases-2026-11-12-traductions.tsv`, renommé) aurait été pris pour des traductions de cartes si l'on rejouait toutes les décisions ; `prep_case.py` lit désormais la table des cas dans `data/de/langue.json` (oubli de l'étape 4).

## Étape 8 : allemand depuis l'anglais, essai A1 (en cours, 12/11/2026, version 1.9.3)

- **Paire en essai** : `data/<L>-<U>/pair.json` = `{"status": "essai"}`. `build.py` publie alors seulement les cartes dont tous les sens sont traduits (ou qui ont une traduction libre), avec leurs chunks et leurs phrases ; une paire sans ce statut doit être complète (sinon erreur, comme avant). `build_app.py` ajoute « essai » en 3e élément de `PAIRS` ; l'appli cache ces paires (`PAIRS_ON`) sauf après une ouverture avec **`?essai=1`** (mémorisé, `mx-essai` ; `?essai=0` le retire). Un niveau sans mots affiche « Bientôt » et ne s'ouvre pas.
- **Crédits** : phrase allemande de Tatoeba traduite par Memolex (pas de traduction anglaise directe sur Tatoeba) = ligne `[n° allemand, auteur, 0, « Memolex »]` ; l'appli affiche « traduction Memolex ». Crédits de-fr et it-fr identiques à l'octet.
- **de-en A1** : 600 mots, 683 sens, 890 traductions anglaises (`glosses.tsv`), 600 chunks, 769 phrases (464 traductions Tatoeba directes, choisies et relues une à une ; 305 traductions Memolex), 89 étiquettes de sens (sur les cartes à plusieurs sens seulement : traduction anglaise du sens étiqueté en français). Traductions libres : *los*, *setzen*, *stimmen*.
- Conventions anglaises : verbes avec « to » (*to live* / *life*), noms sans article, nuance entre parenthèses ; pas de « = » dans une parenthèse (l'appli lit « allemand = traduction » comme une expression : cf. *stimmen* ci-dessous).
- **Dictionnaire provisoire** `dict-de-en.json` (`tools/dict_from_lists.py de en`) : les mots déjà traduits des listes, genre/pluriel/fréquence repris de `dict-de-fr.json`. Le grand dictionnaire allemand-français n'a pas d'équivalent anglais.
- `data/en/utilisateur.json` (articles the/a/an/some, pas d'élision : l'expression de l'appli gère maintenant une liste vide) ; `check_dups` et `chunks_check` lisent les articles de la langue de l'utilisateur (`common.user_art_re`) et tournent pour l'anglais.
- **Interface anglaise** `i18n/en.json` : 575 messages, 0 erreur (`i18n_check`). Textes français restés en dur et désormais traduisibles : crédits (chargement, anonyme, erreur), « N mots » des lots et des niveaux, nom d'un lot de niveau, « N exemples ».
- **Corrigé dans de-fr** : *stimmen* s'affichait « c'est vrai) » au recto (le « = » dans la parenthèse). Nouvelle traduction libre « être exact ; Das stimmt. = c'est vrai » (recto « être exact ; c'est vrai », expression au verso).
- Non-régression (référence 1.9.2) : seules différences = *stimmen* (voulu) et l'état des notifications de l'écran Stats (chargement asynchrone, aléatoire). 0 erreur JavaScript.
- **1.9.4 (retour d'Andrea : français mêlé à l'anglais au verso)** : les textes des cas, écrits en français dans `data/de/langue.json` (« Dat. ou Akk. », « temps (im Mai) : toujours datif »), passent par l'interface (`caseText.*`, 19 messages ; la logique du quiz lit toujours le texte d'origine) ; « singulier », « pluriel : », « N cartes » (réglage du minimum) et le bandeau « DÉJÀ VUE » étaient restés en dur. Balayage de contrôle : tous les mots A1, tous les écrans et une session complète en anglais, sans texte français restant. Français inchangé (non-régression).
- Reste : relecture par échantillon (Andrea), puis A2 à C2 par niveau ; *Wie spricht man mit Frauen?* porte l'étiquette « comme » en de-fr (devrait être « comment »).

## Limites connues (à traiter dans les étapes suivantes)

1. ~~Sens initialisés depuis le français~~ (réglé à l'étape 6 pour l'allemand ; à faire pour l'italien avant sa première paire non française). Un sens = une traduction française de la carte. Parfois ce sont vraiment deux sens (*Erleichterung* : le soulagement / l'allègement), parfois deux traductions du même sens (*sicher* : sûr / certain ; *in* : dans / en). Avant d'ajouter l'anglais, il faut relire les 2 239 mots allemands à plusieurs sens et fusionner les faux doubles (le sens fusionné garde ses deux traductions françaises).
2. ~~Phrases sans numéro Tatoeba~~ : réglé à l'étape 3 (les identifiants internes `clé@n` restent, le numéro Tatoeba est une colonne).
3. **Non migré** : le dictionnaire (`dict-de-fr.json`, 46 029 mots, importé d'une source externe). Il reste tel quel pour l'instant.
4. ~~Grammaire écrite dans l'appli~~ : réglé à l'étape 4 (`data/<L>/langue.json`). Restent écrits pour de/it les **textes du guide** (code couleur, exemples d'aide, sources des listes) : étape 5.
5. **Interface entièrement en français** : tous les textes de l'appli sont écrits en dur. À extraire dans des fichiers de traduction de l'interface.
6. **Langue de l'utilisateur fixée au français** dans l'appli (`dataFile = k-LANG-fr.json`, article français, comparaisons « le / la / l' »).

## Feuille de route

Chaque étape a son critère de sortie. Rien n'est publié tant qu'il n'est pas atteint.

| # | Étape | Critère de sortie |
|---|---|---|
| 1 | Format source + build à l'identique | ✅ 6/6 fichiers identiques |
| 2 | Contrôles sur le format source, par paire (`tools/check.py`) | ✅ sorties identiques sur `data/` et sur les JSON (de-fr, it-fr, contrôles rapides et complets) |
| 3 | Numéros Tatoeba retrouvés pour chaque phrase, crédits générés | ✅ 100 % (de-fr 5 821, it-fr 4 435) ; crédits générés : toutes les paires et tous les auteurs déjà présents dans les anciens crédits, les phrases retirées n'y figurent plus |
| 4 | Grammaire par langue sortie de l'appli (`langue.json`) | ✅ test de non-régression : 0 différence (de, it) |
| 5 | Appli : langue de l'utilisateur variable (`L-U`), interface traduisible | ✅ 5.1 à 5.4 (mécanisme) : appli française inchangée (sauf corrections voulues), textes extraits et prouvés ; traductions au moment de chaque paire |
| 6 | Relecture des sens allemands (fusion des faux doubles) | ✅ 2 222 mots relus ; build de-fr identique à l'octet |
| 7 | Première nouvelle paire : français → anglais ou espagnol (nouvelle liste) | échantillon de 300 cartes ≥ 95 % juste ; contrôles à 0 |
| 8 | Première nouvelle langue d'utilisateur : anglais → allemand (traduction des sens) | A1 en essai (1.9.3) ; puis A2 à C2 ; même seuil |
| … | Une paire à la fois | idem |

## Règles de qualité (rappel)

- Jamais de traduction automatique en passant par le français : chaque paire est rédigée et contrôlée pour elle-même.
- Les nuances, les faux amis, les doublons et les ambiguïtés se contrôlent **par paire** : deux mots allemands distincts en français peuvent se confondre en anglais.
- Seuil de publication par paire : échantillon relu ≥ 95 % de traductions justes ; contrôles automatiques à 0.
- Tout commiter et pousser à la fin de chaque session de travail.
