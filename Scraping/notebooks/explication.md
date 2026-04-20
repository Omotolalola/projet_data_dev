
**1. Convergence de la descente de gradient (gauche)**

La MSE chute brutalement de ~45 à ~0.2 en moins de 200 époques, puis se stabilise parfaitement. C'est exactement ce qu'on veut voir — le modèle a convergé et les 1800 époques restantes ne servent à rien. Ce que tu dois dire dans ton rapport : le learning rate de 0.05 était bien calibré, ni trop grand (oscillations) ni trop petit (convergence lente).

---

**2. Réel vs Prédit (centre)**

Les points s'alignent globalement autour de la diagonale rouge mais avec une dispersion visible. Deux observations importantes :

- Dans la zone **6.2 – 6.8** (prix bas, ~250€–900€), le modèle **surestime** — les points sont au-dessus de la diagonale
- Dans la zone **7.0 – 8.0** (prix hauts, ~1100€–3000€), le modèle **sous-estime** — les points sont en dessous

Cela traduit un **biais systématique** : le modèle a du mal aux extrêmes, ce qui est classique avec peu de features. Le R² de 0.29 se lit ici visuellement.

---

**3. Distribution des résidus (droite)**

Idéalement les résidus doivent être centrés sur 0 et symétriques. Ici deux problèmes visibles :

- La distribution est **légèrement asymétrique à gauche** (queue plus longue vers -0.75), ce qui confirme la surestimation sur les prix bas
- Il y a des résidus jusqu'à **+1.0** (erreurs importantes sur quelques annonces chères), probablement les outliers de luxe que le modèle ne sait pas capturer

---

Le modèle est **correct mais limité**, et c'est une réponse honnête et attendue. Les features disponibles via le scraping (localisation, note, type de logement) expliquent 29% de la variance du prix. Les 71% restants viennent de données non accessibles : surface du logement, nombre de pièces, qualité des photos, équipements. C'est une limite inhérente à la source de données, pas à l'algorithme.