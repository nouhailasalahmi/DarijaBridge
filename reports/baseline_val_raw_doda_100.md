# Baseline : val_raw_doda_100

- Modèle : `facebook/nllb-200-distilled-600M` (ary_Arab vers eng_Latn), 4 faisceaux, découpage `validation`
- Entrée donnée au modèle : `text_darija`
- Phrases évaluées : 100 (au plus 100 par source)

| Source | n | BLEU | chrF | chrF IC 95 % |
|---|---|---|---|---|
| doda | 100 | 0.5 | 9.9 | [8.9 ; 10.8] |
| **Moyenne des sources** | | 0.5 | 9.9 | |
| Toutes phrases confondues | 100 | 0.5 | 9.9 | |

Les scores par source sont à privilégier : DODA domine le jeu de test.

Signatures sacreBLEU : `nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.6.0` ; `nrefs:1|case:mixed|eff:yes|nc:6|nw:0|space:no|version:2.6.0`
