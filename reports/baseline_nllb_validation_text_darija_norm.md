# Baseline : nllb_validation_text_darija_norm

- Modèle : `facebook/nllb-200-distilled-600M` (ary_Arab vers eng_Latn), 4 faisceaux, découpage `validation`
- Entrée donnée au modèle : `text_darija_norm`
- Phrases évaluées : 300 (au plus 100 par source)

| Source | n | BLEU | chrF | chrF IC 95 % |
|---|---|---|---|---|
| atlasia_comments | 100 | 17.4 | 37.2 | [34.0 ; 40.0] |
| atlasia_web_data | 100 | 21.9 | 47.8 | [44.8 ; 50.6] |
| doda | 100 | 6.9 | 30.9 | [27.2 ; 34.5] |
| **Moyenne des sources** | | 15.4 | 38.7 | |
| Toutes phrases confondues | 300 | 19.2 | 42.1 | |

Les scores par source sont à privilégier : DODA domine le jeu de test.

Signatures sacreBLEU : `nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.6.0` ; `nrefs:1|case:mixed|eff:yes|nc:6|nw:0|space:no|version:2.6.0`
