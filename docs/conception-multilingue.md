# Memolex multilingue : conception

État : **étape 1 faite** (11/11/2026). Ce document est la référence ; il est mis à jour à chaque étape.

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

## Limites connues (à traiter dans les étapes suivantes)

1. **Sens initialisés depuis le français.** Un sens = une traduction française de la carte. Parfois ce sont vraiment deux sens (*Erleichterung* : le soulagement / l'allègement), parfois deux traductions du même sens (*sicher* : sûr / certain ; *in* : dans / en). Avant d'ajouter l'anglais, il faut relire les 2 239 mots allemands à plusieurs sens et fusionner les faux doubles (le sens fusionné garde ses deux traductions françaises).
2. **Phrases sans numéro Tatoeba.** Les identifiants sont provisoires (`clé@n`). Pour proposer la même phrase aux anglophones ou aux hispanophones, il faut retrouver le numéro Tatoeba de chaque phrase (export Tatoeba accessible depuis l'atelier) et récupérer ses traductions dans les autres langues. Les crédits seront alors générés automatiquement, au lieu de l'actuel `credits-*.json` figé.
3. **Non migrés** : le dictionnaire (`dict-de-fr.json`, 46 029 mots, importé d'une source externe) et les crédits. Ils restent tels quels pour l'instant.
4. **Grammaire écrite dans l'appli** : `LANGS`, `ART_RE`, `PREP_CASE`, couleurs de genre, tout cela est dans `index.html` et pensé pour de/it. À déplacer dans un fichier de description par langue (`data/<L>/langue.json` : genres, articles, élision, cas, ce qu'on fait deviner).
5. **Interface entièrement en français** : tous les textes de l'appli sont écrits en dur. À extraire dans des fichiers de traduction de l'interface.
6. **Langue de l'utilisateur fixée au français** dans l'appli (`dataFile = k-LANG-fr.json`, article français, comparaisons « le / la / l' »).

## Feuille de route

Chaque étape a son critère de sortie. Rien n'est publié tant qu'il n'est pas atteint.

| # | Étape | Critère de sortie |
|---|---|---|
| 1 | Format source + build à l'identique | ✅ 6/6 fichiers identiques |
| 2 | Contrôles sur le format source (`check_dups`, chunks, pluriels, faux amis… adaptés à `data/`), par paire | mêmes résultats que sur les JSON (0 doublon, 0 ambiguïté) |
| 3 | Numéros Tatoeba retrouvés pour chaque phrase, crédits générés | ≥ 99 % des phrases Tatoeba retrouvées ; crédits identiques ou plus complets |
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
