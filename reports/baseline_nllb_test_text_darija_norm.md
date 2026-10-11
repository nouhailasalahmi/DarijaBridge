# Baseline : nllb_test_text_darija_norm

- Modèle : `facebook/nllb-200-distilled-600M` (ary_Arab vers eng_Latn), 4 faisceaux, découpage `test`
- Entrée donnée au modèle : `text_darija_norm`
- Phrases évaluées : 895 (au plus 300 par source)

| Source | n | BLEU | chrF | chrF IC 95 % |
|---|---|---|---|---|
| atlasia_comments | 300 | 15.2 | 35.6 | [33.6 ; 37.6] |
| atlasia_web_data | 295 | 20.0 | 46.0 | [44.3 ; 47.7] |
| doda | 300 | 8.4 | 30.5 | [28.0 ; 32.8] |
| **Moyenne des sources** | | 14.5 | 37.4 | |
| Toutes phrases confondues | 895 | 17.2 | 40.2 | |

Les scores par source sont à privilégier : DODA domine le jeu de test.

Signatures sacreBLEU : `nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.6.0` ; `nrefs:1|case:mixed|eff:yes|nc:6|nw:0|space:no|version:2.6.0`
