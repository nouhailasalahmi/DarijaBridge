# Rapport de découpage

Découpage par groupe (hash du texte Darija) : validation 10%, test 10%, sel `darijabridge-v1`.

- Groupes : 71706
- **Groupes présents dans plusieurs découpages : 0** (doit valoir 0)

## Tâche : Darija vers `en`

| Source | train | validation | test |
|---|---|---|---|
| atlasia_comments | 7720 | 995 | 903 |
| atlasia_stories | 36 | 4 | 4 |
| atlasia_web_data | 2343 | 299 | 295 |
| doda | 38482 | 4758 | 4827 |
| **Total** | 48581 (80.1 %) | 6056 (10.0 %) | 6029 (9.9 %) |

Phrases de test dont la traduction apparaît aussi dans train : 541 sur 6029 (courtes réponses génériques du type « Yes. », sans fuite du Darija).

## Tâche : sans traduction (Darija seul)

| Source | train | validation | test |
|---|---|---|---|
| doda | 15 | 0 | 4 |
| madar_rabat | 9455 | 1240 | 1217 |
| **Total** | 9470 (79.4 %) | 1240 (10.4 %) | 1221 (10.2 %) |

