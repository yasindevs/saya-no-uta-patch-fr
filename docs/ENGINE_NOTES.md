# The Song of Saya (Steam/GOG remake) — notes de reverse engineering

> Objectif : comprendre le moteur pour **recréer un engine de VN rétro en C++**.
> Dernière mise à jour : 2026-09-06

---

## 1. Identification du moteur

Le jeu tourne sur le moteur maison de **Nitroplus**, appelé **N2 / N4** (classes C++ internes
dans le namespace `Diesel`, archives gérées par `Mware`).

Symboles RTTI trouvés dans `Saya_en.exe` :

```
.?AVCFont@Diesel@@
.?AVCBitmapFont@Diesel@@
.?AVCSystemFont@Diesel@@
.?AVCFontPool@Diesel@@
.?AVCArchiveNPK@Mware@@
.?AVCFilePackedObjectNPK@Mware@@
```

Fichiers binaires du jeu :

| Fichier | Rôle |
|---|---|
| `Saya_en.exe` | moteur (Diesel/N4) |
| `Mware.dll` | couche I/O + archives NPK |
| `libogg / libvorbis / libvorbisfile.dll` | audio Ogg Vorbis |
| `*.npk` | archives chiffrées (cg, sound, voice, script, system, font, N4_sys) |

Archives attendues par l'exe (chaînes trouvées) : `cg.npk`, `sound.npk`, `voice.npk`,
`script.npk`, `system.npk`, `dx.npk`, `N4_sys.npk`, et `patch/*.npk`.

> `patch/*.npk` est intéressant : le moteur charge des archives de patch qui **écrasent** les
> fichiers de base. C'est la voie propre pour modder/traduire sans toucher aux .npk originaux.

---

## 2. Format d'archive : NPK2

Header (little-endian) :

```
offset  taille  champ
0x00    4       magic "NPK2"
0x04    4       version / unk (= 2)
0x08    16      IV (AES-CBC)
0x18    4       file_count
0x1C    4       table_size (taille de la table chiffrée)
0x20    ?       table d'index, AES-256-CBC chiffrée
...             données des segments (AES-256-CBC + raw deflate optionnel)
```

Entrée de la table (après déchiffrement) :

```
1  byte   inutilisé
2  u16    name_size
n  bytes  name (Shift-JIS, chemin virtuel ex. "media/font/droidserif-regular.ttf")
4  u32    taille du fichier décompressé
32 bytes  SHA-256 du fichier décompressé  (à recalculer si on modifie le fichier)
4  u32    segment_count
  puis, par segment :
  8  u64  offset absolu dans le .npk
  4  u32  size_aligned  (taille chiffrée sur disque, multiple de 16)
  4  u32  size_comp     (taille compressée réelle)
  4  u32  size_orig     (taille décompressée)
```

Règles :
- Chaque segment est déchiffré **AES-256-CBC** avec la même clé et le **même IV** que la table.
- Si `size_comp != size_orig` → **raw deflate** (`zlib.decompress(data, -15)`), sinon stocké brut.
- Segments découpés à **65536 octets** max en pratique.

### Clé AES-256 (Saya no Uta JAST/Steam/GOG)

```
d0b71f3c4e24cecfddeea91d24b0403229a3e5330d2951826051d6c94af5af54
```

### Outils

[`tools/npk2.py`](../tools/npk2.py) lit et écrit les archives (taille + SHA-256 recalculés) :

```bash
python tools/npk2.py x "C:/GOG Games/The Song of Saya/system.npk" media_out
```

Le moteur charge aussi **`patch/*.npk`** par-dessus les archives de base (vérifié en jeu) :
c'est ce qu'utilise le patch FR. Exception : `setting.ini` (dans `system.npk`) est lu avant
le montage des patchs, on ne peut donc pas changer le titre de la fenêtre par ce biais.

---

## 3. La font du jeu

`font.npk` ne contient **qu'un seul fichier** :

```
media/font/droidserif-regular.ttf   (172 532 octets)
```

Table `name` du TTF :

| Champ | Valeur |
|---|---|
| Family | **Droid Serif** |
| Subfamily | Regular |
| Full name | Droid Serif |
| PostScript | DroidSerif |
| Version | 1.00 |
| Manufacturer | Ascender Corporation (digitized data © 2007 Google) |
| Licence | **Apache License 2.0** — réutilisable librement |

Extraite dans : `C:\GOG Games\The Song of Saya\media\font\droidserif-regular.ttf`

Successeur moderne quasi identique en dessin, avec bien plus de glyphes : **Noto Serif**.

### Comment le moteur l'utilise
- Chargée en mémoire via l'API Win32 **`AddFontMemResourceEx`** (donc pas d'installation système),
  puis instanciée avec **`CreateFontW`** → rendu GDI dans une surface, pas de FreeType.
- Répertoire virtuel : `media/font/`
- Alias côté script (`framework/constantvalue.nut`) :
  - `DEFAULT_FONT_NAME` = `n4_default_font`
  - `DEFAULT_FONT_RUBY_NAME` = `n4_default_ruby_font` (ruby = furigana)
- API Squirrel : `setFont`, `setFontDirect`, `setRubyFont`, `setFontColor`,
  `getFaceName`, `getRubyFaceName`, `loadFont` / `unloadFont`, `clearFontCache`.
- Charsets supportés : `SYSTEM_FONT_CHARSET_{ANSI,OEM,SJIS,HANGUL,GB2312,CHINESEBIG5,GREEK,TURKISH,BALTIC,RUSSIAN,EASTEUROPE,MAC,SYMBOL}`
- Ombre de texte : `FONT_SHADOW_TYPE_{NONE,UP,DOWN,LEFT,RIGHT,LEFT_UP,LEFT_DOWN,RIGHT_UP,RIGHT_DOWN,AROUND}`
  → le look du jeu = **Droid Serif + contour/ombre `AROUND`** sur une box semi-transparente.

---

## 4. Architecture logicielle

Deux couches de script, toutes deux dans `script.npk` sous `media/script/`.

### 4.1 Couche framework — **Squirrel** (`.nut`, bytecode compilé)

75 fichiers :

```
main.nut
framework/
  n2framework.nut          point d'entrée du framework
  constantvalue.nut        toutes les constantes (FONT_*, NUT_TYPE_*, SYSTEM_FONT_CHARSET_*)
  app/capp.nut             application / boucle principale
  command/                 système de commandes (CCommand, Action, Get/Set/Request/Wait/Delete)
                           + bindfunction / mathfunction / utilityfunction / load-save nutfunction
  nut/                     LE scene graph — "Nut" = node
    cnutbase, cnutmanager, cnutprocess
    2D   : cnutsprite, cnutsurface, cnuttext, cnutmask, cnutshademask, cnutline
    UI   : cnutuibase, cnutuicontainer, cnutbutton, cnutstatebutton, cnutslider, cnutlistview
    3D   : cnutmodel, cnutmodelcharacter, cnutsprite3d, cnutcamera, cnutpointlight,
           cnutbone, cnutjoint, cnutnull3d, cnutrigidbody, cnutparticle, cnutdisplacementmap
    div  : cnutsound, cnutsound3d, cnutcapture, cnutfile
  math/    vec2, vec3, quat
  font/    cfont.nut  (m_FaceName, m_RubyFaceName, getFaceName, getRubyFaceName)
  scene/   cscene.nut
  script/  cscript.nut, cscriptmanager.nut     <- l'interpréteur .nps
  sound/   csounddevice.nut
  texture/ catlasinfo.nut, catlasinfomanager.nut   <- atlas de textures
  physics/ cphysics.nut
  des/     cdes.nut
system/
  boot.nut, boot_start.nut, n1_system.nut
  sys_textbox.nut, sys_backlog.nut, sys_menu.nut, sys_savedata.nut,
  sys_after_load.nut, sys_load_error.nut, sys_calc.nut, sys_key.nut
product/
  product_config.nut, product_dialog.nut, product_saveload.nut,
  product_sskip.nut, product_var.nut
```

Points notables :
- Le moteur est **3D-capable** (modèles, os, physique, particules, lumières) même si le VN
  n'utilise quasiment que la couche 2D → héritage d'un moteur généraliste Nitroplus.
- `catlasinfo` → les sprites sont packés en **atlas**.
- `product_config.nut` expose `BacklogTextFont`, `font_setting`, `face_icon_enable`.

### 4.2 Couche scénario — **NPS** (`.nps`, texte brut, style HTML)

39 fichiers dans `media/script/nps/` : `sy010.nps` … `sy200madend.nps`, plus
`menu.nps`, `cg.nps`, `music.nps`, `include.h`.

Encodage : **UTF-8**, texte narratif + balises `<TAG ATTR="value">` **insensibles à la casse**.
Commentaires en `//`. `include.h` contient des `<DEFINE SRC="..." DEST="...">` (macros).

#### Balises rencontrées (fréquence sur le jeu complet)

| Balise | Occ. | Attributs observés | Rôle |
|---|---|---|---|
| `<K>` / `<k>` | 2569 | — | **click-wait** (attend l'input joueur, fin de page) |
| `<voice>` | 1452 | `name`, `SRC` | joue la voix ; `name` = nom du perso (JP) |
| `<wipe>` | 884 | `EFFECT`, `TIME` | transition (ex. `fade`), `TIME` en ticks |
| `<background>` | 577 | `SRC`, `shade` | fond ; `shade` = variante d'éclairage |
| `<wait>` | 521 | `time` | pause |
| `<clear>` | 482 | — | vide la scène/le texte |
| `<box>` | 464 | `type` | style de la boîte de dialogue |
| `<se>` | 366 | `id`, `src`, `mode`, `loop` | effet sonore sur canal `id` |
| `<bustup>` | 249 | `NAME`, `face`, `MODE`, `zoom`, `ALIGN` | sprite perso (`ALIGN=left/center/right`) |
| `<bgm>` | 214 | `src`, `mode`(fadein/fadeout), `old`, `time`, `loop` | musique |
| `<a>` | 139 | `HREF`, `OPERATOR` | saut (`fichier#MARKER` ou `#MARKER`) + effet de bord |
| `<marker>` | 123 | `NAME` | label de saut |
| `<choice>` | 89 | `HREF`, `FILE`(liste `;`), `x`, `y`, `TYPE`, `SHORTCUT`, `ONSE`, `PUSHSE` | bouton cliquable (frames d'anim dans `FILE`) |
| `<i>` | 56 | — | italique / inline |
| `<system>` | 50 | `MENU`, `INIT`, `cmd`(ex. `cgmode`), `list`, `next*`, `back*` | fonction système |
| `<flash>` | 21 | `SRC`(couleur), `WAIT`, `COUNT`, `EFFECT`, `TIME` | flash plein écran |
| `<layer>` | 12 | `NUM`, `SRC`(image ou `#rrggbb`), `TRANSPARENT` | calque/overlay coloré |
| `<select>` | 11 | `cursorname` (`fichier.png#frames`) | mode sélection (curseur animé) |
| `<calc>` | 10 | `WORKNAME`, `OPERATOR`, `MODE`(`global`) | variables de flags/scénario |
| `<end>` | 4 | — | fin de bloc/route |
| `<center>` | 2 | — | texte centré |
| `<scroll>` `<movie>` `<load>` `<include>` | 1 chacun | — | divers |

Autres conventions :
- Les lignes de texte narratif commencent par 2 espaces (indentation d'affichage).
- `SRC` de voix : `"2\000104"` → dossier `2`, id `000104` (chemin Windows dans le script).
- Beaucoup de noms d'assets/SE sont en **japonais**.

---

## 5. Rendu / look "rétro"

Ce qui donne l'aspect visuel de la version Steam :
1. **Droid Serif** (empattements, gris très clair) — pas une font système.
2. Contour/ombre autour des glyphes (`FONT_SHADOW_TYPE_AROUND`) pour lisibilité sur tout fond.
3. Boîte de dialogue **semi-transparente à coins arrondis** (`<box type="N">`, ~9 styles).
4. Fonds CG avec **grain/bruit** + `shade` par scène.
5. Bustups PNG alpha, alignés `left`/`right`, `face` (expression) commutable sans recharger.
6. Transitions `<wipe EFFECT="fade">` très courtes (8–30 ticks).

---

## 6. Plan de réimplémentation C++

### Stack minimale
- **SDL3** (fenêtre, input, audio) ou SDL2.
- **stb_image** (PNG) ou SDL_image.
- **FreeType** + **HarfBuzz** (shaping), ou `stb_truetype` si Latin seul.
  Le jeu original utilise GDI ; FreeType donnera un rendu plus propre/portable.
- **stb_vorbis** / libvorbis pour l'Ogg.
- **miniaudio** ou SDL_audio pour le mixage multicanal (BGM + N canaux SE + voix).

### Découpage suggéré
```
core/      Archive (NPK2 reader), FileSystem virtuel, Log
gfx/       Renderer2D (quads + atlas), Texture, Sprite, Transition/Wipe
text/      FontManager (FreeType), TextLayout (wrap, ruby/furigana), TextBox (typewriter)
audio/     AudioEngine, BgmChannel, SeChannel[], VoiceChannel
script/    NpsLexer -> NpsParser -> commandes ; VM à coroutine (une commande par frame)
scene/     SceneGraph "Nut"-like (node + transform + z), UI (Button, Slider, ListView)
game/      SaveData, Backlog, ConfigMenu, CGGallery, MusicRoom, Flags/Variables
```

### Ordre de travail conseillé
1. **NPK2 reader en C++** (AES-CBC + miniz pour l'inflate) → lire les assets directement
   depuis les `.npk`, sans tout extraire.
2. **Parser NPS** : lexer de balises `<tag attr="v">` + texte. Sortie = flux de commandes typées.
   Sous-ensemble suffisant (>95% des occurrences) : `background`, `bustup`, `box`, `wipe`,
   `wait`, `k`, `clear`, `bgm`, `se`, `voice`, `marker`, `a`, `calc`, `choice`.
3. **VM à coroutine** : `Update(dt)` exécute des commandes jusqu'à une commande bloquante
   (`<k>`, `<wait>`, `<choice>`). État sérialisable = (fichier, index de commande, flags, scène)
   → la **sauvegarde** devient triviale.
4. **Renderer** : layers fixes → BG, bustups (L/C/R), overlay/layer, textbox, UI.
5. **Textbox** : typewriter char par char, wrap, `<k>` = attente, backlog (ring buffer),
   skip / auto-mode.
6. Menus : title, save/load (vignettes), config, CG gallery (`<system cmd="cgmode">`), music room.

### Pièges identifiés
- Balises **case-insensitive**, attributs dans un ordre libre → parser tolérant.
- Chemins avec `\` (Windows) dans les scripts → normaliser.
- Noms d'assets en japonais → tout en **UTF-8**, ne repasser en Shift-JIS que pour la table NPK.
- Le même IV est réutilisé pour tous les segments (faiblesse crypto, mais pratique ici).
- `<voice>` porte aussi le **nom du locuteur** → c'est lui qui alimente l'affichage du nom.

---

## 7. Légal

- **Droid Serif** est sous Apache 2.0 → réutilisable dans ton propre moteur sans souci.
- Le **code du moteur, les CG, la musique, les voix et le scénario** restent propriété de
  Nitroplus / JAST. Écrire ton propre moteur est une chose, redistribuer les assets en est une
  autre : garde le moteur **séparé des assets** (il lit les `.npk` de la copie légitime).

---

## 8. TODO / pistes non explorées

- [ ] Extraire `system.npk` (279 Ko) et `N4_sys.npk` (8 Mo) → assets d'UI, shaders, atlas.
- [ ] Format des images dans `cg.npk` (PNG brut ou format Nitroplus propriétaire ?).
- [ ] Décompiler le bytecode Squirrel des `.nut` pour lire `sys_textbox.nut`
      (dimensions/styles exacts des `<box type>`).
- [ ] Documenter les 9 `<box type>` et la liste complète des `EFFECT` de `<wipe>`.
- [ ] Tester le mécanisme `patch/*.npk` pour injecter une traduction proprement.
