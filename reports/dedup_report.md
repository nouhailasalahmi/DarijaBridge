# Rapport de déduplication

## Bilan par source

| Source | Lus | Gardés | Rejetés | Taux de rejet |
|---|---|---|---|---|
| doda | 48698 | 48086 | 612 | 1.3 % |
| madar_rabat | 11922 | 11912 | 10 | 0.1 % |
| atlasia_comments | 9716 | 9618 | 98 | 1.0 % |
| atlasia_web_data | 2942 | 2937 | 5 | 0.2 % |
| atlasia_stories | 44 | 44 | 0 | 0.0 % |
| **Total** | 73322 | 72597 | 725 | 1.0 % |

## Rejets par raison

| Raison | doda | madar_rabat | atlasia_comments | atlasia_web_data | atlasia_stories |
|---|---|---|---|---|---|
| duplicate_in_source | 612 | 10 | 83 | 5 | 0 |
| duplicate_other_source | 0 | 0 | 15 | 0 | 0 |

## Groupes (même texte Darija)

- Groupes distincts : 71706
- Groupes avec plusieurs enregistrements (plusieurs traductions) : 771
- Plus grand groupe : 6 enregistrements

Le découpage entraînement / validation / test devra garder chaque groupe entier d'un seul côté.

## Textes Darija communs à plusieurs sources

| Paire de sources | Textes Darija en commun |
|---|---|
| doda / madar_rabat | 110 |
| atlasia_comments / doda | 21 |
| atlasia_comments / madar_rabat | 4 |
