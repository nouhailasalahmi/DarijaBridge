# Comparaison : val_raw_doda_100 (A) contre nllb_validation_text_darija_norm (B)

- Phrases communes : 100 (A : 100, B : 100), source : doda
- Rééchantillonnages appariés : 1000

| Métrique | A | B | Écart (B moins A) | IC 95 % de l'écart | B meilleur dans |
|---|---|---|---|---|---|
| chrf | 9.9 | 30.9 | +21.1 | [+17.3 ; +25.1] | 100 % des tirages |
| bleu | 0.5 | 6.9 | +6.5 | [+2.6 ; +10.5] | 100 % des tirages |

L'écart de chrF est probablement réel (l'intervalle ne contient pas 0).
