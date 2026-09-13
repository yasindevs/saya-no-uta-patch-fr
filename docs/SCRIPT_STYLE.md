# Style d'écriture des scripts `.nps` — The Song of Saya

> **But de ce document** : pouvoir écrire ou traduire du `.nps` qui *sonne* comme l'original,
> et savoir quel effet le scénariste emploie dans quelle situation.
> Complément narratif de [`ENGINE_NOTES.md`](ENGINE_NOTES.md) (qui décrit le *moteur*) et de
> [`TEXTBOX_LAYOUT.md`](TEXTBOX_LAYOUT.md) (qui décrit le *rendu*).
>
> Base : lecture des 38 fichiers `sy*.nps` (~338 000 caractères de texte narratif).
> `sy010.nps` est déjà traduit en FR — tous les exemples anglais ci-dessous viennent des autres fichiers.
> Dernière mise à jour : 2026-09-09

---

## 1. Anatomie d'un fichier

Tous les fichiers d'histoire suivent le même squelette, sans exception :

```
//匂坂邸：郁紀                                   ← commentaire d'en-tête : LIEU：POV
<MARKER NAME="#14">                              ← marqueur de chapitre (numéro de scène)
<bgm src="s01" mode="fadeout" time="20" loop="off">   ← on coupe la musique du chapitre précédent
<clear>
<WIPE EFFECT="fade" TIME="20">
<wait time="900">                                ← ~9 s de noir + silence entre deux chapitres
<bgm src="s07" mode="fadein" old="fadeout" time="10" COUNT="1;-1" LOOP="on">
<BACKGROUND SRC="bb01no0">//
<WIPE EFFECT="fade" TIME="20">
<wait time="200">
<box type="9">
  Dr. Tanbo Ryoko has never had a more troublesome patient.

   … le corps de la scène …

<A HREF="sy150.nps" OPERATOR="">                 ← DERNIÈRE ligne : enchaînement vers le fichier suivant
```

- L'en-tête `//` utilise **le deux-points pleine chasse `：`** (U+FF1A) : `//大学：瑶`, `//廃墟：耕司`.
  Format = `//<lieu>：<personnage dont on suit le point de vue>`.
- `<MARKER NAME="#N">` numérote la scène (`#1` … `#20`). Les fichiers de branche ont en plus
  un marqueur nommé en japonais : `#郁紀`, `#凉子`, `#合流`, `#badend`, `#madend`.
- Un fichier ne se termine **jamais** sur du texte : toujours `<A HREF="…">` (ou `<END>` pour une fin).
- Les fins ferment par `<SYSTEM MENU="#FFE">` + `<SYSTEM CMD="ending" ROLL="staff">` + `<END>`.

---

## 2. Les quatre registres de texte

| Registre | Forme exacte | Exemple |
|---|---|---|
| **Narration** | ligne commençant par **exactement 2 espaces** | `··His voice is hard and flat, his words tossed carelessly into the air.` |
| **Dialogue** | `<voice …>` + 2 espaces + `"…"` sur **la même ligne** | `<voice NAME="凉子" SRC="4\000106">··"Any changes since your last visit?"<K>` |
| **Dialogue + incise** | idem, la narration continue *après* la citation, même ligne | `··"Yes, of course," Ryoko answers, smiling to cover up her irritation.` |
| **Pensée intérieure** | `<I>…</I>`, sans guillemets | `··<I>I should've brought more smokes.</I>` |

Statistiques d'indentation sur tout le jeu : **3 345 lignes à 2 espaces**, 671 à 0 (= balises pures),
14 exceptions (3 espaces = suite d'une ligne coupée dans l'éditeur, 16 espaces = un unique effet
de centrage manuel, `sy010.nps:144`).

### Règles de ponctuation de page

- **ligne vide = un temps** (respiration entre deux paragraphes). Deux lignes vides = pause plus marquée.
- `<K>` = **attente de clic**. En mode NVL, le texte **ne s'efface pas** : il s'accumule dans la boîte.
- `<clear>` = **nouvelle page**. C'est lui qui vide, pas `<K>`.
- Il y a **2 452 `<K>`** et **117 `<k>`** minuscules : les deux sont équivalents (balises insensibles à la
  casse), la minuscule sert surtout aux coupures *au milieu* d'une réplique (voir §4).

### Rythme mesuré

| Grandeur | Médiane | Moyenne |
|---|---|---|
| Caractères entre deux `<K>` | **120** | 143 |
| Caractères par page (`<clear>` à `<clear>`) | **473** | 679 |

→ un « bloc de clic » = **1 à 3 phrases**, jamais plus. Une page = **3 à 5 blocs**.
C'est la respiration la plus caractéristique du texte : très court, très cadencé.

---

## 3. Voix narratives

| Personnage POV | Personne | Temps |
|---|---|---|
| **Fuminori** (郁紀) | **1ʳᵉ personne** — « I » | présent |
| Ryoko (凉子), Koji (耕司), Yoh (瑶), Yosuke (洋佑), Omi (青海) | **3ᵉ personne limitée** | présent |

Le présent est utilisé **partout**, y compris pour l'action et l'horreur. Le passé n'apparaît que
pour les antécédents (« Treatment of subdural hematoma […] **had been** the only way to save… »).

- Un changement de POV = **un nouveau fichier** (annoncé dans l'en-tête `//`), ou un `<clear>` +
  changement de fond à l'intérieur d'un fichier (ex. `sy010.nps` bascule de Fuminori à Yoh en cours de route).
- Les personnages japonais sont nommés **nom de famille en premier** dans la narration
  (*Sakisaka Fuminori*, *Tanbo Ryoko*, *Ogai Masahiko*), mais par leur prénom dans les dialogues
  (« Fuminori », « Koji », « Doctor »).
- La narration à la 3ᵉ personne dit **« Ryoko »**, **« Koji »**, jamais « le docteur » ou « notre héros ».

---

## 4. Le dialogue

### Découpe d'une réplique longue (117 occurrences)

Un même fichier de voix est coupé en deux morceaux pour placer une attente de clic **au milieu** de
la réplique. Le second morceau porte le suffixe `_2` (parfois `_3`) et commence par **un seul espace** :

```
<voice NAME="凉子" SRC="4\000806">  "Normally, I would never say anything to frighten a patient...<K><voice name="凉子" SRC="4\000806_2"> but there have been reports of serious neurological disorders post-surgery. We must continue to monitor your condition carefully."<K>
```

C'est l'outil de suspense n°1 du script : la phrase se casse toujours sur `...` ou sur une virgule,
juste avant l'information qui fait mal.

### Conventions de ponctuation orale

| Effet | Écriture | Exemple |
|---|---|---|
| Hésitation | `...` (3 points, **416** occ.) | `"I... heard it from a nurse,"` |
| Silence total | `......` (6 points, **47** occ., souvent seuls sur la ligne) | `<voice name="凉子" SRC="4\001806">  "......"<K>` |
| Bégaiement / peur | lettre + `-` + espace | `"R- Really?"` · `"I- Is someone here?"` · `"A- Alright..."` |
| Interruption brutale | `―` (U+2015) collé | `"I WAnt tO heLP YOu! wE aLl DO! SO plEAse, teLL M―"` |
| Cri | majuscules dans une phrase normale | `"Die! Die! DIE!"` |

---

## 5. Typographie

- **`―` U+2015 HORIZONTAL BAR** — 210 occurrences. **Toujours collé, jamais d'espace autour** :
  `MRI―Magnetic Resonance Imaging―is a way for doctors…` ·
  `The girl's choking gasps, the despair in her eyes―they only intensify his ecstasy.`
  C'est *le* signe de ponctuation signature du texte (incise brutale, apposition, coupure).
  ⚠️ Ce n'est **pas** un em-dash `—` (U+2014) : si tu traduis, garde U+2015 pour rester cohérent
  avec la fonte et la métrique d'origine.
- **`<I>…</I>`** — 56 occurrences, trois usages seulement :
  1. **pensée intérieure entière** : `<I>Now then, where should I leave off to go shopping?</I>`
  2. **un seul mot mis en relief** : `The bones are too small, and there are <I>too</I> many of them.` ·
     `Could Saya <I>actually</I> be reading my charts?`
  3. **titres d'œuvres** : `<I>Traite des Chiffres</I>`, `<I>Voynich Manuscript</I>`, `<I>True Scary Stories: Hospital Edition</I>`
- Pas de ruby / furigana dans les `.nps` (le moteur le supporte pourtant : `setRubyFont`).
- Pas de gras, pas de couleur de texte inline.
- Curiosité : `sy120.nps:407` contient `<I>Oh...<II><K>` — `<II>` est très probablement une coquille
  pour `</I>` (c'est la seule balise italique non fermée du jeu).

---

## 6. Le gimmick central : la dégradation du langage

C'est **le** procédé d'écriture du jeu, et il est entièrement porté par le texte, pas par le moteur.
Trois niveaux, strictement corrélés au point de vue :

### Niveau 1 — charabia total

Fuminori entend, mais ne décode rien. Uniquement au tout début (`sy010.nps`, 14 répliques) et
2 rappels tardifs (`sy070`, `sy160`).

```
<voice name="青海" SRC="2\000104">  "H#Y," the wriggling mass of flesh burbles, "*G$Hsy%3whY&Xtr1p%3?"<K>
<voice name="瑶" SRC="2\000205">  "SK%guj!%~? &YGo^#1sGjisKIREs5#%0sK473?"<k>
<voice name="耕司" SRC="2\000302">  "H#H#. K$5GiVe52fdf%^#TSU+BA. HI#~TG^Sk5tI#GR3NSTLY."<k>
```

Règles observées :
- longueur et ponctuation **de vraies phrases** : ça se termine par `.` `?` `!`, ça a des espaces
  aux bons endroits. On doit *voir* que c'est de la parole.
- substitutions leetspeak : `1`→l/i, `3`→e, `5`→s, `0`→o, `4`→a, `7`→t.
- symboles autorisés : `# % $ & ^ @ * ! ? ; : + ~` et les répétitions finales `@@@`, `###`, `!!!!`.
- des fragments de vrais mots restent lisibles (`GiVe`, `SnoW`, `ScRed`) — le lecteur croit
  entrapercevoir du sens. C'est volontaire.

### Niveau 2 — casse aléatoire

Fuminori a appris à décoder les mots, mais les voix restent inhumaines. La **casse est randomisée
lettre par lettre**, ~50/50, sans motif ; l'orthographe et la ponctuation restent parfaites.

```
<voice name="耕司" SRC="…">  "hEy FuMInoRi," dit l'une des bêtes de chair… "QuE pENses-tU De touT ça ?"
<voice name="瑶"  SRC="…">  "I Feel rEAlLy bad ABoUT YOur PareNTs. BUt yoU'RE Not aLONE."
<voice name="洋佑" SRC="…">  "GOOD EVeniNg. aRE YOu just GeTtIng hOME?"
```

### Niveau 3 — texte normal

### La règle d'or : l'inversion

| Scène vue par | Les humains parlent | Saya parle |
|---|---|---|
| **Fuminori** | niveau 1 puis 2 (monstrueux) | **niveau 3, normal, chaleureux, enfantin** |
| **N'importe qui d'autre** | niveau 3, normal | **niveau 2 (monstrueux)** |

```
(POV Yosuke, sy080.nps)
<box type="5">
<voice name="沙耶" SRC="16\000201">"CALm doWn. DOn't BE sCarEd."
```

C'est la seule information que le jeu ne donne jamais explicitement : elle est **entièrement portée
par la typographie**. Si tu traduis, ne « nettoie » jamais ces lignes.

### Où la distorsion apparaît (comptage)

| Fichier | Charabia (niv. 1) | Casse aléatoire (niv. 2) | Locuteurs concernés |
|---|---|---|---|
| `sy010` | 14 | 5 | 耕司 Koji |
| `sy030` | — | 4 | 瑶 Yoh |
| `sy040` | — | 1 | 沙耶 Saya |
| `sy060` | — | 7 | 洋佑 Yosuke |
| `sy070` | 2 | — | — |
| `sy080` | — | 8 | 沙耶, 妻, 博美 |
| `sy160` | 2 | — | — |
| `sy187f` | — | 5 | 瑶 Yoh |
| `sy200madend` | — | 1 | 沙耶 Saya |

> La distorsion ne touche **que le dialogue entre guillemets**. La narration, même en POV Fuminori,
> reste dans un anglais parfaitement clair et littéraire. Le contraste est le sujet du jeu.

---

## 7. Les idiomes de mise en scène

Le script réutilise une poignée de blocs quasi à l'identique. Les connaître = pouvoir écrire une
scène qui se fond dans l'original.

### 7.1 Changement de plan (≈ 480 occurrences)

```
<clear>
<BACKGROUND SRC="bp01me0" shade="4">//
<WIPE EFFECT="fade" TIME="10">
<wait time="200">
<box type="9">
```

> Le `//` en fin de ligne `<BACKGROUND>` est un reliquat d'édition présent sur la majorité des lignes
> de fond. Sans effet, mais présent partout : reproduis-le si tu veux du diff propre.

### 7.2 Changement d'expression (≈ 250 occurrences)

```
<BUSTUP NAME="沙耶" face="困り笑い1" MODE="on" zoom="" ALIGN="center">
<WIPE EFFECT="fade" TIME="5">
<voice name="沙耶" SRC="28\003201"> "Don't worry. There's no danger."<K>
```

Un bustup est **toujours** immédiatement suivi de son propre `<WIPE fade 5>`, puis de la réplique.
`ALIGN` : `left` = Koji / Yoh / Fuminori, `right` = Omi / Fuminori (interlocuteur), `center` = **Saya, toujours**.

### 7.3 Grammaire des durées de `<WIPE>`

| `TIME` | Usage | Occ. |
|---|---|---|
| `0` | coupe franche (souvent avec `EFFECT="NORMAL"`) | ~100 |
| `5` | changement d'expression (bustup) | 215 |
| `10` | changement de plan / de fond | **455** |
| `20` | ouverture / fermeture de chapitre, moment lourd | 97 |
| `30`, `40` | exceptionnel (fins) | 2 |

Idem pour `<wait>` : `200` après un fondu de plan, `900` entre deux chapitres.

### 7.4 SE collé *dans* la phrase (33 occurrences)

Le son est déclenché exactement au mot, sans casser la ligne :

```
  And when his tears have run dry and his heart is calm, <se id="1" src="車山道発進" mode="normal" loop="off">Koji starts up his car and drives away.
  As I wonder what she has in store for me,<se id="2" NAME="瑶" SRC="28\002905a" mode="normal" loop="off" vol="50"> the sound of crying reaches my ears. I stiffen.
```

Convention de canaux : **`id="1"` = bruitage ponctuel** (`loop="off"`), **`id="2"` = ambiance / boucle**
(`loop="on"`, parfois avec `vol=`).

### 7.5 Le flash de choc (21 occurrences)

Toujours la même paire, toujours sur de la violence :

```
<se id="1" src="鈴見攻撃2" mode="normal" loop="off">
<FLASH SRC="#ffffff" WAIT="1" COUNT="3" EFFECT="normal" TIME="0">
```

`COUNT="1"` = un impact, `COUNT="3"` = acharnement. Un seul `SRC="#ff0000"` dans tout le jeu.

### 7.6 Voix sur une ligne de **narration**

```
<voice name="洋佑" SRC="18\001403">  Yosuke grabs the bone and twists with all his might. The monster convulses and gurgles…
```

Pas de guillemets : le fichier voix est un râle, un cri, un souffle joué **sous** la narration.
Très fréquent dans les scènes d'horreur.

### 7.7 `<box type="5">` — la petite boîte

Trois usages, tous « hors monde » :

1. la voix déformée de Saya entendue par un tiers ;
2. les **SMS de Saya** sur le téléphone, avec `<center>` pour les réponses de Fuminori :
   ```
   <box type="5">
   <center>"I will. Thank you.<K>
      Goodbye, Fuminori."</center>
   ```
3. une réplique isolée qui doit frapper seule à l'écran
   (`"If you want to know about Sakisaka Fuminori, come to his house alone. Tell no one."`).

⚠️ Dans `box type="5"`, le texte **n'est pas indenté** de 2 espaces.
(440 `box type="9"` contre 23 `box type="5"` et un unique `type="8"`.)

### 7.8 `<LAYER>` — teinte d'ambiance

`<LAYER SRC="#000000" TRANSPARENT="75" NUM="1">` assombrit avant un écran de choix ;
`#ff0000 / 50` (rage), `#000099 / 80` (nuit), `#99cc44 / 50` (malaise). `<LAYER SRC="" NUM="1">` efface.

### 7.9 Effets à usage unique

- `<scroll num="0" x="800" time="10" count="40">` — une seule fois (`sy200madend`), pour un
  panoramique brutal au moment du coup de feu.
- `<MOVIE SRC="Nitro_LOGO.mpg" SKIP="ON">` — logo d'ouverture.

---

## 8. Nommage des assets (à respecter)

### Fonds

`b` + lieu (1-2 lettres) + `NN` + **ambiance** + `0` — ex. `bp01me0`, `bb01no0`, `bg04ni0`.

| Suffixe | Occ. | Sens | `shade` |
|---|---|---|---|
| `me` | 103 | **la vision déformée de Fuminori** | **toujours `shade="4"`** |
| `no` | 77 | normal / jour | — |
| `ni` | 35 | nuit | — |
| `xx` | 13 | neutre, abstrait | — |

> `shade="4"` apparaît **104 fois et jamais ailleurs** que sur un fond `…me0`.
> C'est le marqueur visuel du POV Fuminori : un simple attribut porte tout le concept du jeu.
> (La lecture `me`/`no`/`ni`/`xx` est déduite de cette corrélation, pas d'une doc officielle.)

Les fonds purement numériques (`13`, `32`, `35`, `03_1`, `43_1`, `51`) sont des **CG d'événement**.

### Voix

`SRC="<chapitre>\<NNNN><ID locuteur>"` — les **2 derniers chiffres identifient le personnage** :

| ID | Personnage | Répliques |
|---|---|---|
| `00` | 郁紀 Fuminori | 402 |
| `01` | 沙耶 Saya | 347 |
| `02` | 耕司 Koji | 278 |
| `06` | 凉子 Ryoko | 235 |
| `05` | 瑶 Yoh | 99 |
| `03` | 洋佑 Yosuke | 38 |
| `04` | 青海 Omi | 33 |
| `07` | 妻 (l'épouse) | 11 |
| `08` | 博美 Hiromi | 7 |

Suffixes : `_2` / `_3` = découpe d'une réplique longue, `a` = variante / prise alternative.

### Expressions (`face=`)

Vocabulaire japonais **compositionnel** : base (`通常` neutre, `困惑` trouble, `にっこり` sourire,
`きょとん` perplexe, `険しい` dur, `激怒` fureur, `目逸らし` regard fuyant, `寂しげ` mélancolique)
+ modificateur (`ムス` boudeur, `笑い` rire, `1`/`2` variantes). Ex. `目逸らし笑い2`, `弱気目寂しげ`.

### Bruitages (`se src=`)

Descriptions japonaises littérales : `本めくり` (page tournée), `携帯ボタン` (touche de téléphone),
`臭気` (puanteur), `斧風切り1` (sifflement de hache), `車ドア開閉` (portière). Ne pas traduire :
ce sont des noms de fichiers.

---

## 9. Structure de branchement

Le jeu n'a que **deux choix**, et ils sont écrits de la même façon : la dernière ligne de narration
laisse une phrase **en suspens**, et les options la terminent.

```
(sy090.nps, dernière ligne)
  I...

(sy100sl.nps)
<LAYER SRC="#000000" TRANSPARENT="75" NUM="1">
<WIPE EFFECT="fade" TIME="2">
<CHOICE HREF="sy101end.nps" TEXT="...want it all back." OPERATOR=""></A>//
<CHOICE HREF="sy103.nps"    TEXT="...don't need it anymore." OPERATOR=""></A>//
```

Le second choix (`sy170sl.nps`) suit exactement le même patron : « appeler Fuminori » /
« appeler Ryoko ».

- Le drapeau est posé par `<CALC WORKNAME="badend" OPERATOR="1">` et propagé par
  `<A HREF="sy190badend.nps" OPERATOR="badend=1">`.
- Convention de nommage des branches : suffixe **`f`** = branche 郁紀 (**F**uminori),
  suffixe **`r`** = branche 凉子 (**R**yoko). Ex. `sy173f.nps` / `sy173r.nps`, `sy184f` / `sy184r`.
- Les lignes `//<A HREF="#合流">` en commentaire dans presque tous ces fichiers montrent que la
  version 2003 tenait tout dans un seul script ; le remake l'a éclaté en fichiers, en gardant les
  anciens sauts en commentaire. Les marqueurs `#合流`, `#合流2`, `#合流3`, `#合流4` = « point de
  convergence » des branches.
- Les fichiers de branche portent souvent un en-tête explicite en japonais :
  `//＜＜以下、郁紀に電話したルートのみ＞＞`.

---

## 10. Checklist « écrire dans ce style »

- [ ] En-tête `//lieu：POV` avec `：` pleine chasse, puis `<MARKER>`, puis le bgm.
- [ ] Narration = **2 espaces** d'indentation, présent, 3ᵉ personne (sauf Fuminori = « je »).
- [ ] Dialogue **sur la même ligne** que son `<voice>`, guillemets droits `"`.
- [ ] Un bloc entre deux `<K>` = **1 à 3 phrases, ~120 caractères**. Ne jamais laisser courir.
- [ ] Ligne vide entre chaque temps ; `<clear>` seulement au changement de plan.
- [ ] Couper les répliques longues en `_2` / `_3` avec le `<K>` juste avant la révélation.
- [ ] `―` (U+2015) collé pour les incises et les interruptions ; `......` pour le silence.
- [ ] `<I>` réservé à la pensée, au mot souligné, au titre d'œuvre.
- [ ] Distorsion typographique **jamais dans la narration**, et respect de l'inversion Saya / humains.
- [ ] Bloc de plan complet : `<clear>` / `<BACKGROUND …>//` / `<WIPE fade 10>` / `<wait 200>` / `<box type="9">`.
- [ ] Bustup toujours suivi de `<WIPE fade 5>` ; Saya toujours `ALIGN="center"`.
- [ ] Fond `…me0` ⇒ `shade="4"` obligatoire (POV Fuminori).
- [ ] Dernière ligne du fichier = `<A HREF="…">`, jamais du texte.
