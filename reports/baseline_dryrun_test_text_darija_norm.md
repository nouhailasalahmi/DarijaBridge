# Baseline : dryrun_test_text_darija_norm

- Modèle : `facebook/nllb-200-distilled-600M` (ary_Arab vers eng_Latn), 4 faisceaux, découpage `test`
- Entrée donnée au modèle : `text_darija_norm`
- Phrases évaluées : 895 (au plus 300 par source)

| Source | n | BLEU | chrF | chrF IC 95 % |
|---|---|---|---|---|
| atlasia_comments | 300 | 0.1 | 0.1 | [0.1 ; 0.2] |
| atlasia_web_data | 295 | 0.0 | 0.1 | [0.0 ; 0.1] |
| doda | 300 | 0.2 | 0.1 | [0.0 ; 0.1] |
| **Moyenne des sources** | | 0.1 | 0.1 | |
| Toutes phrases confondues | 895 | 0.1 | 0.1 | |

Les scores par source sont à privilégier : DODA domine le jeu de test.

Signatures sacreBLEU : `nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.6.0` ; `nrefs:1|case:mixed|eff:yes|nc:6|nw:0|space:no|version:2.6.0`
