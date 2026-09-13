"""Aligne le texte FR (01.utf, PONScripter) sur les unités de texte des .nps (Steam/GOG).

Principe :
1. Les répliques doublées portent le même identifiant de voix des deux côtés → ancres sûres.
2. Entre deux ancres, on aligne les blocs restants par programmation dynamique
   (méthode de Gale & Church sur les longueurs), avec fusion / découpe de phrases.

Sortie : un dict  clé_unité -> texte FR  +  la liste des alignements non triviaux à relire.
"""
import math
import re
import collections

from formats import TAG_RE

RATIO = 1.15      # longueur FR ≈ 1.15 × longueur EN
VAR = 6.8

# coûts a priori des types de « perles » (−log P, Gale & Church)
BEADS = {
    (1, 1): -math.log(0.89),
    (1, 2): -math.log(0.089 / 2), (2, 1): -math.log(0.089 / 2),
    (1, 3): -math.log(0.01), (3, 1): -math.log(0.01),
    (2, 2): -math.log(0.011),
    (0, 1): -math.log(0.0099), (1, 0): -math.log(0.0099),
}


def plain_len(s):
    return max(1, len(TAG_RE.sub('', s).strip()))


def length_cost(len_en, len_fr):
    if len_en == 0 and len_fr == 0:
        return 0.0
    mean = (len_en + len_fr / RATIO) / 2
    z = (len_fr / RATIO - len_en) / math.sqrt(VAR * max(mean, 1))
    # −log de la proba bilatérale d'une normale
    pd = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return -math.log(max(pd, 1e-12))


TERM_PENALTY = 1.5


def dp_align(en, fr, en_term=None, fr_term=None):
    """en, fr : listes de longueurs ; *_term : 'k' (attente de clic) ou 'p' (fin de page)
    pour chaque bloc. Retourne une liste de perles (i0, di, j0, dj)."""
    n, m = len(en), len(fr)
    en_term = en_term or ['k'] * n
    fr_term = fr_term or ['k'] * m
    INF = float('inf')
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if cost[i][j] == INF:
                continue
            for (di, dj), prior in BEADS.items():
                ni, nj = i + di, j + dj
                if ni > n or nj > m:
                    continue
                c = cost[i][j] + prior + length_cost(sum(en[i:ni]), sum(fr[j:nj]))
                if di and dj and en_term[ni - 1] != fr_term[nj - 1]:
                    c += TERM_PENALTY
                if c < cost[ni][nj]:
                    cost[ni][nj] = c
                    back[ni][nj] = (i, j)
    beads, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        beads.append((pi, i - pi, pj, j - pj))
        i, j = pi, pj
    return list(reversed(beads))


SENT_END = re.compile(r'(?<=[.!?…"」])\s+(?=\S)|(?<=\.\.\.)\s+(?=\S)|(?<=―)(?=\S)')
SOFT_END = re.compile(r'(?<=[,;:])\s+')


def split_text(text, weights):
    """Découpe `text` en len(weights) morceaux, aux frontières de phrases les plus proches
    des proportions données. Retourne (morceaux, qualité) ; qualité 'phrase'|'virgule'|'espace'."""
    parts = len(weights)
    if parts == 1:
        return [text], 'phrase'
    total = sum(weights)
    L = len(text)
    targets = []
    acc = 0
    for w in weights[:-1]:
        acc += w
        targets.append(L * acc / total)
    quality = 'phrase'
    cuts = []
    for rx, q in ((SENT_END, 'phrase'), (SOFT_END, 'virgule'), (re.compile(r'\s+'), 'espace')):
        cands = [m.start() for m in rx.finditer(text)]
        if len(cands) >= parts - 1:
            quality = q
            chosen, last = [], -1
            for t in targets:
                pool = [c for c in cands if c > last]
                if not pool:
                    break
                c = min(pool, key=lambda c: abs(c - t))
                chosen.append(c)
                last = c
            if len(chosen) == parts - 1:
                cuts = chosen
                break
    if not cuts:
        return [text] + [''] * (parts - 1), 'echec'
    out, prev = [], 0
    for c in cuts:
        out.append(text[prev:c].strip())
        prev = c
    out.append(text[prev:].strip())
    return out, quality


def align(nps_units, ons_units):
    """nps_units : liste globale ordonnée d'NpsUnit. ons_units : liste d'OnsUnit.
    Retourne (fr_par_unité: list[str|None], rapport: list[dict])."""
    vmap = collections.defaultdict(list)
    for i, u in enumerate(ons_units):
        if u.voice:
            vmap[u.voice].append(i)

    anchors, last = [(-1, -1)], -1
    for j, u in enumerate(nps_units):
        if u.voice and u.voice in vmap:
            cands = [i for i in vmap[u.voice] if i > last]
            # garde-fou : on refuse un saut énorme (voix dupliquée hors séquence)
            if cands and cands[0] - last < 400:
                anchors.append((j, cands[0]))
                last = cands[0]
    anchors.append((len(nps_units), len(ons_units)))

    fr = [None] * len(nps_units)
    src = [[] for _ in nps_units]     # indices ONS ayant servi à chaque unité NPS
    report = []
    for (j1, i1), (j2, i2) in zip(anchors, anchors[1:]):
        if 0 <= j1 < len(nps_units):
            fr[j1] = ons_units[i1].text
            src[j1].append(i1)
        seg_n = list(range(j1 + 1, j2))
        seg_o = list(range(i1 + 1, i2))
        if len(seg_n) == len(seg_o):
            for a, b in zip(seg_n, seg_o):
                fr[a] = ons_units[b].text
                src[a].append(b)
            continue
        en_l = [plain_len(nps_units[a].text) for a in seg_n]
        fr_l = [plain_len(ons_units[b].text) for b in seg_o]
        en_t = ['k' if nps_units[a].suffix else 'p' for a in seg_n]
        fr_t = ['p' if ons_units[b].term == '\\' else 'k' for b in seg_o]
        for (ni, di, oj, dj) in dp_align(en_l, fr_l, en_t, fr_t):
            ns = seg_n[ni:ni + di]
            os_ = seg_o[oj:oj + dj]
            texts = [ons_units[b].text for b in os_]
            entry = {'bead': f'{di}:{dj}', 'nps': ns, 'ons': os_}
            for a in ns:
                src[a].extend(os_)
            if di == 1 and dj >= 1:
                fr[ns[0]] = ' '.join(t.strip() for t in texts)
            elif di >= 1 and dj == 1:
                pieces, q = split_text(texts[0].strip(), [plain_len(nps_units[a].text) for a in ns])
                entry['split'] = q
                for a, p in zip(ns, pieces):
                    fr[a] = p
            elif di == 2 and dj == 2:
                for a, b in zip(ns, os_):
                    fr[a] = ons_units[b].text
            elif di == 0 and dj == 1:
                # bloc FR sans équivalent : on l'accroche au bloc NPS précédent
                tgt = seg_n[ni - 1] if ni > 0 else (j1 if j1 >= 0 else None)
                entry['attach_to'] = tgt
                if tgt is not None:
                    fr[tgt] = (fr[tgt] or '').rstrip() + ' ' + texts[0].strip()
                    src[tgt].extend(os_)
            elif di == 1 and dj == 0:
                entry['missing'] = True
            report.append(entry)
    return fr, report, anchors, src
