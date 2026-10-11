# Baseline : nllb_validation_text_darija_ar_ref

- Modèle : `facebook/nllb-200-distilled-600M` (ary_Arab vers eng_Latn), 4 faisceaux, découpage `validation`
- Entrée donnée au modèle : `text_darija_ar_ref`
- Phrases évaluées : 100 (au plus 100 par source)

- Ignorées (champ d'entrée ou référence absents) : {'atlasia_comments': 995, 'atlasia_web_data': 299}

| Source | n | BLEU | chrF | chrF IC 95 % |
|---|---|---|---|---|
| doda | 100 | 7.0 | 31.4 | [27.5 ; 35.5] |
| **Moyenne des sources** | | 7.0 | 31.4 | |
| Toutes phrases confondues | 100 | 7.0 | 31.4 | |

Les scores par source sont à privilégier : DODA domine le jeu de test.

Signatures sacreBLEU : `nrefs:1|case:mixed|eff:no|tok:13a|smooth:exp|version:2.6.0` ; `nrefs:1|case:mixed|eff:yes|nc:6|nw:0|space:no|version:2.6.0`
