# Rapport de normalisation

## Translittération Arabizi vers arabe (jeu de test DODA mis de côté)

Lexique appris sur 43754 phrases (39867 mots), évalué sur 4944 phrases mises de côté.

| Méthode | Mots corrects | CER | Phrases exactes | Mots inconnus du lexique | Exactitude sur mots inconnus |
|---|---|---|---|---|---|
| Règles seules | 67.0 % | 12.2 % | 21.7 % | - | - |
| Lexique + règles | 83.4 % | 6.0 % | 48.0 % | 15.5 % | 48.5 % |

## Répartition des écritures par source

| Source | Enregistrements | arabic | latin | mixed | none | Mots latins hors lexique (moyenne) | Avec arabe de référence | Dont identique à la prédiction |
|---|---|---|---|---|---|---|---|---|
| doda | 48698 | 0 | 48698 | 0 | 0 | 2.8 % | 48698 | 31776 |
| madar_rabat | 11922 | 11922 | 0 | 0 | 0 | - | 0 | 0 |
| atlasia_comments | 9716 | 8227 | 1414 | 72 | 3 | 45.5 % | 0 | 0 |
| atlasia_stories | 44 | 44 | 0 | 0 | 0 | - | 0 | 0 |
| atlasia_web_data | 2942 | 2940 | 0 | 2 | 0 | 90.0 % | 0 | 0 |
