# NVL textbox — spécification exacte (Song of Saya, remake Steam/GOG)

Toutes les valeurs viennent des `.ini` du moteur, extraits de `system.npk` →
copiés dans `media/system/`. Les assets UI sont dans `media/ui/`.

---

## 0. Le canvas : 1280 × 960

`media/system/setting.ini` :

```ini
[Init]
SCREEN_WIDTH=1280
SCREEN_HEIGHT=960
WINDOW_NAME="Song of Saya"
SOUND_TYPE="XAudio2"

[Font]
Droid Serif="media/font/DroidSerif-Regular.ttf"
```

Confirmé par les backgrounds : `media/cg/bp01me0.png` = **1280×960**.

> **Toutes les coordonnées de ce document sont dans l'espace 1280×960.**
> Le launcher propose 1920×1440 = exactement **×1.5**.
>
> **Recommandation forte pour ton moteur** : rends tout dans une render target
> 1280×960, puis blitte-la scalée vers la fenêtre. C'est ce que fait le moteur
> original, et ça garantit un layout au pixel près à n'importe quelle résolution
> (sinon `fontSize=32` × 1.5 = 48 mais `fontRowSpace=11` × 1.5 = 16.5 → arrondi
> → dérive de la mise en page sur une page de 18 lignes).

Note historique : dans les `.ini`, chaque valeur est suivie d'un commentaire
`#NNN` = la valeur d'origine de la version 2003 en 800×600. Le rapport est **×1.6**.
`system.ini` a gardé `width=800 / height=600` (legacy, ignoré au profit de `setting.ini`).

---

## 1. La boîte noire — `media/system/textbox.ini`

### Le modèle

```
BoxLeft, BoxTop ─────────────────────────────┐
│  ← MarginLeft →                            │  ▲
│  ┌──────────────────────────────────────┐  │  │
│  │                                      │  │  │
│  │            ZONE DE TEXTE             │  │ BoxHeight
│  │                                      │  │  │
│  └──────────────────────────────────────┘  │  │
│                          ← MarginRight →   │  ▼
└─────────────────── BoxWidth ───────────────┘
```

- L'image `framename` est dessinée **à (BoxLeft, BoxTop), à sa taille native**,
  avec une opacité de `transparency` %.
- La zone de texte = le rect de la box moins les 4 marges.

```
textX      = BoxLeft + MarginLeft
textY      = BoxTop  + MarginTop
textWidth  = BoxWidth  - MarginLeft - MarginRight     ← largeur de wrap
textHeight = BoxHeight - MarginTop  - MarginBottom
```

### BOX9 — **c'est celui du mode NVL narratif** (`<box type="9">`, le plus utilisé)

| Champ | Valeur (1280×960) | ×1.5 (1920×1440) |
|---|---|---|
| BoxLeft | **64** | 96 |
| BoxTop | **80** | 120 |
| BoxWidth | **1152** | 1728 |
| BoxHeight | **800** | 1200 |
| MarginLeft | **32** | 48 |
| MarginTop | **10** | 15 |
| MarginRight | **16** | 24 |
| MarginBottom | **10** | 15 |
| framename | `data\f05.png` | — |
| transparency | **50** | — |

Donc :
- **Cadre** : rect `(64, 80)` → `(1216, 880)`, soit 1152×800
- **Texte** : origine `(96, 90)`, largeur de wrap **1104 px**, hauteur utile **780 px**
- Avec un pas de ligne de 49 px (voir §2) → **15 lignes** par page max

### Tous les autres BOX

| ID | Left | Top | W | H | ML | MT | MR | MB | frame | opac. | usage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 64 | 80 | 1152 | 800 | 32 | 10 | 16 | 10 | f05.png | (100) | NVL opaque |
| 1 | 198 | 360 | 885 | 493 | 261 | 107 | 16 | 53 | — | 100 | face à gauche |
| 2 | 13 | 326 | 885 | 541 | 264 | 104 | 16 | 53 | — | 100 | face à gauche |
| 3 | 384 | 326 | 886 | 541 | 16 | 104 | 262 | 53 | — | 100 | face à droite |
| 4 | 198 | 24 | 886 | 493 | 16 | 107 | 267 | 53 | — | 100 | face à droite (haut) |
| 5 | 64 | 80 | 1152 | 800 | 320 | 240 | 320 | 240 | f05.png | 50 | texte centré |
| 6 | 0 | 512 | 768 | 320 | 16 | 10 | 16 | 10 | f02.png | 100 | petit, bas-gauche |
| 7 | 512 | 512 | 768 | 320 | 16 | 10 | 16 | 10 | f06.png | 100 | petit, bas-droite |
| 8 | 64 | 640 | 1152 | 312 | 16 | 10 | 16 | 10 | f03.png | 100 | **ADV bas d'écran** |
| **9** | **64** | **80** | **1152** | **800** | **32** | **10** | **16** | **10** | **f05.png** | **50** | **NVL (le tien)** |

Les BOX1–4 ont une grosse marge d'un côté : c'est la place réservée à l'icône
de visage. Position de ces icônes dans `media/system/face.ini` (`Left`/`Top` +
`message` = l'ID de BOX associé).

### Les images de cadre — `media/ui/f0*.png`

Analysées pixel par pixel :

| Fichier | Taille | Contenu |
|---|---|---|
| `f05.png` | **1152×800** | noir pur `#000000`, alpha 255, coins arrondis |
| `f03.png` | 1152×312 | idem |
| `f06.png` | 768×320 | idem |
| `f01.png` | 768×272 | idem |
| `f02.png` | 1152×312 | idem |

**Ce sont juste des rectangles noirs opaques à coins arrondis.** Rien d'autre :
pas de dégradé, pas de bordure, pas de texture. Toute la translucidité vient
de `transparency=50`.

- Couleur intérieure : `RGBA(0, 0, 0, 255)` uniforme
- **Rayon des coins = 12 px** (mesuré : à y=0 le remplissage commence à x=9,
  à y=9 il commence à x=0 — ça colle exactement à un cercle de rayon 12 antialiasé)
- La taille de `f05.png` (1152×800) est **exactement** BoxWidth×BoxHeight de BOX9
  → l'image est blittée 1:1, aucun scaling ni 9-slice.

Tu n'as donc **pas besoin de l'image** : un `roundRect(64, 80, 1152, 800, r=12)`
rempli en `rgba(0,0,0,0.5)` donne le même rendu.

> **`transparency` = opacité en %**, pas transparence. Preuve : `backlog.ini`
> a `transparency=100` pour le fond du backlog, qui est bien opaque en jeu.

---

## 2. Le texte — `media/system/system.ini`, section `[メッセージ]`

```ini
fontName        = "Droid Serif"
rubyName        = "Droid Serif"
fontSize        = 32
rubySize        = 12
fontPitch       = 0      # espacement additionnel entre caractères
fontRowSpace    = 11     # espacement additionnel entre lignes
fontRubyOffset  = 2
color           = "#FFFFFF"   # texte normal
read_color      = "#B3B3B3"   # texte déjà lu (gris)
blink1          = "data\cur01.png#5"
blink2          = "data\cur00.png#7"
blink3          = "data\cur03_auto.png#12"
blink4          = "data\cur03_auto.png#12"
blinkTime       = 2
```

### Métriques dérivées

⚠️ **`fontRowSpace` s'ajoute à la hauteur de ligne naturelle de la font, PAS à
la taille d'em.** Le moteur rastérise via GDI (`CreateFontW`), et pour une font
créée à une taille d'em de 32, GDI rapporte
`tmHeight = round(usWinAscent) + round(usWinDescent)`.

Métriques de Droid Serif (unitsPerEm = 2048) :

| Champ | Unités | à 32 px |
|---|---|---|
| `hhea.ascender` / `OS/2.usWinAscent` | 1901 | 29.70 → **30** |
| `hhea.descender` / `OS/2.usWinDescent` | −483 / 483 | 7.55 → **8** |
| `hhea.lineGap` | 0 | 0 |
| `OS/2.sCapHeight` | 1462 | 22.84 |

```
tmHeight    = 30 + 8 = 38
lineAdvance = tmHeight + fontRowSpace = 38 + 11 = 49 px
advanceX    = glyphAdvance + fontPitch      (fontPitch = 0 ici)
```

(L'hypothèse naïve `fontSize + fontRowSpace = 43` donne 64.5 px à ×1.5 et
comprime la page d'environ 12 % — l'écart saute aux yeux en comparaison directe.)

### Vérification sur le jeu en cours d'exécution

Mesuré par capture d'écran du jeu lancé en plein écran sur un moniteur
2560×1440 (bande noire de 320 px de chaque côté → contenu 1920×1440, soit
×1.5 depuis le canvas), sur une scène de 4 lignes de texte :

| Grandeur | Attendu (canvas) | Mesuré (écran) | Mesuré (canvas) |
|---|---|---|---|
| Bord gauche de la plaque | 64 | 415 | **63.3 – 64.0** ✓ |
| Bord droit | 1216 | 2143 | **1215.3 – 1216.0** ✓ |
| Bord haut | 80 | 119 | **79.3** ✓ |
| Bord bas | 880 | 1319 | **879.3** ✓ |
| Pas de ligne | 49 | 74.0 (moy. sur 3 intervalles) | **49.3** ✓ |

La géométrie de BOX9 est donc confirmée au pixel, et le pas de ligne à 0.5 px
près — l'écart résiduel vient du fait que le haut de bande dépend du glyphe le
plus haut de chaque ligne. `43` donnerait 64.5 px écran, soit 9.5 px d'erreur
par ligne : exclu.

Méthode : bords de plaque par gradient horizontal/vertical moyenné (la plaque
à 50 % produit une marche nette sur un décor clair), lignes de texte par
densité de transitions horizontales. Un seuillage de luminosité ne marche pas —
il attrape le grain du CG, qui a sa propre période.

### Position du texte pour BOX9

```
origine  = (96, 90)
wrap     = 1104 px
ligne n  : y = 90 + n * 49       (n = 0 .. 15)
```

Le `y` est le **haut de la ligne** ; la baseline est à `y + ascent(32px)`.

### Détail : l'indentation de début de paragraphe

Elle **ne vient pas du moteur** : dans les `.nps`, chaque ligne de narration
commence par **2 espaces littéraux**. C'est ce qui produit le petit décrochage
visible au début de chaque paragraphe. Ne le code pas en dur.

### Couleur "déjà lu"

`read_color = #B3B3B3` : quand tu relis un passage déjà vu, le moteur rend le
texte en gris au lieu de blanc. C'est par **passage** (flag de lecture stocké
dans la save globale), pas par caractère.

### L'effet d'ombre / contour

L'API existe côté script (`framework/font/cfont.nut`) :

```
m_ShadowType             // FONT_SHADOW_TYPE_{NONE,UP,DOWN,LEFT,RIGHT,
                         //   LEFT_UP,LEFT_DOWN,RIGHT_UP,RIGHT_DOWN,AROUND}
m_ShadowColor
m_ShadowGap              // distance/décalage
m_ShadowPower            // intensité
m_ShadowAlphaExponent    // courbe de falloff
setShadow(), setShadowColor(), setShadowShadingParameter(alpha_exp)
```

⚠️ **Les valeurs ne sont pas dans les scripts ni dans les `.ini`.** J'ai dumpé le
bytecode Squirrel de `cfont.nut` : il ne contient **aucun littéral numérique**.
Les valeurs par défaut sont donc en dur dans le C++ du moteur (`Saya_en.exe`).

Ce qu'on peut dire visuellement (screenshots) : halo sombre **tout autour** du
glyphe, doux (pas un contour net de 1 px), légèrement plus dense en bas-à-droite
→ cohérent avec `FONT_SHADOW_TYPE_AROUND`, petit gap, falloff exponentiel.

**Recette de repro** (à ajuster à l'œil sur une capture) :
1. Rendre le glyphe en noir dans une texture offscreen.
2. Dilater de ~2 px (ou blur gaussien σ ≈ 1.5).
3. Appliquer `alpha = pow(alpha, alphaExponent)` avec `alphaExponent ≈ 0.6–0.8`
   (c'est exactement ce que fait `m_ShadowAlphaExponent`).
4. Composer à ~70 % d'opacité, puis le glyphe blanc par-dessus.

Alternative bon marché et très proche : 8 passes du glyphe en noir à alpha 0.35
sur un cercle de rayon 2, puis le glyphe blanc.

---

## 3. Le CTC (click-to-continue)

Ce sont des **sprite sheets horizontales**, une frame = **38×38 px**.
Le nombre de frames est le suffixe `#N` dans `system.ini`.

| Clé | Fichier | Taille | Frames | Aspect |
|---|---|---|---|---|
| `blink1` | `media/ui/cur01.png` | 190×38 | **5** (38×38) | vrille/liane **verte** |
| `blink2` | `media/ui/cur00.png` | 266×38 | **7** (38×38) | feuille **bleu-vert** |
| `blink3` | `media/ui/cur03_auto.png` | 456×38 | **12** (38×38) | mode **auto** |
| `blink4` | `media/ui/cur03_auto.png` | 456×38 | **12** (38×38) | mode auto |

`blinkTime = 2` → **2 ticks moteur par frame**. À 60 fps ça donne une animation
à 30 fps ; le cycle complet de `cur00` (7 frames) dure 14 ticks ≈ 0.23 s.

### Placement

L'icône est dessinée **inline, au caret de texte** : juste après le dernier
glyphe écrit, sur la ligne courante. C'est visible sur tes deux screenshots —
la feuille suit la fin du texte, elle n'est pas ancrée à un coin de la box.

```
iconX = caretX  (+ un petit gap, ~0)
iconY = ligneCourante.y + (lineAdvance - 38) / 2     // centrage vertical
```

Avec `lineAdvance = 43` et une icône de 38 → `iconY = ligne.y + 2 ou 3`.

> Si tu préfères un vrai bouton comme tu le disais : garde l'icône animée inline
> (c'est la signature visuelle du jeu) et rends **toute la box cliquable** pour
> avancer — c'est ce que fait l'original. Un bouton dédié dans un coin est
> possible mais casse le look.

### Quelle icône quand
`blink1`/`blink2` = attente de clic, `blink3`/`blink4` = mode auto.
Les deux premières correspondent probablement à « attente en milieu de page »
et « attente en fin de page » (`<k>` vs fin de bloc) — tes deux screenshots
montrent bien deux icônes différentes (verte / bleue) selon le moment.

---

## 4. Le reste de l'UI (bonus, même source)

**Skip** (`system.ini`) : `data\skip.png` (686×234) à `(0, 0)`, opacité 70.

**Vignettes de save** : 160×120. Confirmé : `media/cg/mode/*.png` sont en 160×120.

**Alignement des bustups** (`align.ini`) — c'est le **centre X** du sprite :

| nom | X |
|---|---|
| `center` | 640 |
| `left` | 384 |
| `right` | 896 |

**Backlog** (`backlog.ini`) : box `(0,0)` 1280×780, marges L54 T74 R265 B0,
fond `data\log\backlogback.png`, opacité 100, Droid Serif 32, rowSpace 10.
Boutons REW/FF/Return alignés en colonne à droite (x ≈ 1043 et 1147).

**Choix** (`choice.ini`) : voile de fond `data\black.jpg` à 75 %.
Boutons 928×70 à `x=176`, `y` ∈ {320, 480} (2 choix) ou {432, 576, 736, 864}.
Frames `Select01.png` (normal) / `Select02.png` (survol + pressé).
Couleur texte `#7D7D7D`, survol `#00FFFF`.

**Format des CG** : chaque image est un couple **`nom.png` (RGB) + `nom_a.png`
(masque alpha séparé)**, tous deux en 1280×960. Pense-y dans ton loader.

---

## 5. Constantes prêtes à coller (C++)

```cpp
// ── Canvas ────────────────────────────────────────────────────────────────
constexpr int  CANVAS_W = 1280;
constexpr int  CANVAS_H = 960;      // 4:3 ; blit scalé vers la fenêtre

// ── NVL textbox (BOX9) ────────────────────────────────────────────────────
struct BoxStyle {
    int  left, top, width, height;
    int  marginL, marginT, marginR, marginB;
    float opacity;            // 0..1
    float cornerRadius;
};
constexpr BoxStyle BOX_NVL { 64, 80, 1152, 800,  32, 10, 16, 10,  0.50f, 12.0f };
constexpr BoxStyle BOX_ADV { 64, 640, 1152, 312, 16, 10, 16, 10,  1.00f, 12.0f };

// zone de texte de BOX_NVL
constexpr int TEXT_X = 64 + 32;                      //   96
constexpr int TEXT_Y = 80 + 10;                      //   90
constexpr int TEXT_W = 1152 - 32 - 16;               // 1104  (largeur de wrap)
constexpr int TEXT_H = 800  - 10 - 10;               //  780

// ── Texte ─────────────────────────────────────────────────────────────────
constexpr const char* FONT_FILE   = "media/font/droidserif-regular.ttf";
constexpr int   FONT_SIZE         = 32;
constexpr int   FONT_PITCH        = 0;               // ajout par caractère
constexpr int   FONT_ROW_SPACE    = 11;              // ajout par ligne
// tmHeight = round(usWinAscent*size/upem) + round(usWinDescent*size/upem)
// Droid Serif @32px : 30 + 8 = 38
constexpr int   FONT_LINE_HEIGHT  = 38;             // dépend de la font !
constexpr int   LINE_ADVANCE      = FONT_LINE_HEIGHT + FONT_ROW_SPACE;  // 49
constexpr int   MAX_LINES         = TEXT_H / LINE_ADVANCE;             // 15
constexpr uint32_t COLOR_TEXT     = 0xFFFFFFFF;      // #FFFFFF
constexpr uint32_t COLOR_READ     = 0xFFB3B3B3;      // #B3B3B3
constexpr int   RUBY_SIZE         = 12;
constexpr int   RUBY_OFFSET       = 2;

// ── CTC ───────────────────────────────────────────────────────────────────
constexpr int CTC_FRAME_W    = 38;
constexpr int CTC_FRAME_H    = 38;
constexpr int CTC_TICKS_PER_FRAME = 2;               // blinkTime
// cur01.png : 5 frames | cur00.png : 7 frames | cur03_auto.png : 12 frames
// dessiné inline au caret : (caretX, lineY + (LINE_ADVANCE - CTC_FRAME_H) / 2)

// ── Bustups ───────────────────────────────────────────────────────────────
constexpr int ALIGN_LEFT_X = 384, ALIGN_CENTER_X = 640, ALIGN_RIGHT_X = 896;
```

---

## 6. Fichiers de référence sur disque

| Chemin | Contenu |
|---|---|
| `media/system/*.ini` | les 8 `.ini` du moteur (textbox, system, setting, align, backlog, choice, face, game) |
| `media/ui/f0*.png` | les cadres noirs arrondis |
| `media/ui/cur0*.png` | les sprite sheets CTC |
| `media/ui/skip.png` | l'indicateur de skip |
| `media/font/droidserif-regular.ttf` | la font |
| `npk2_unpack.py` | extracteur NPK2 complet |
| `npk2_grep.py` | extracteur sélectif : `python npk2_grep.py cg.npk "motif" [dossier_sortie]` |

Voir aussi [ENGINE_NOTES.md](ENGINE_NOTES.md) pour le format NPK2, le format
de script NPS et l'architecture générale du moteur.
