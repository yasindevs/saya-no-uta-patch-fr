"""Rapport de relecture des alignements douteux.

usage : python review.py <dossier_nps_original> <01.utf> <sortie.txt> [overrides.json]

Pour chaque groupe suspect : les blocs EN (clé fichier:ligne:n) et les lignes FR de 01.utf
(ons:N) qui les couvrent, puis l'affectation actuelle. Les clés déjà présentes dans
overrides.json sont ignorées.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_alignment import load_nps  # noqa: E402
from formats import parse_ons, TAG_RE  # noqa: E402
from align import align  # noqa: E402
from generate import is_gibberish  # noqa: E402


def main():
    nps_dir, ons_path, out_path = sys.argv[1:4]
    done = set()
    if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
        ov = json.load(open(sys.argv[4], encoding='utf-8'))
        done = set(ov.get('units', {})) | set(ov.get('ok', []))
    units, keys = load_nps(nps_dir)
    ons = parse_ons(open(ons_path, encoding='utf-8-sig').read())
    fr, rep, anchors, src = align(units, ons)

    def plain(s):
        return TAG_RE.sub('', s or '').strip()

    def ratio(j):
        en = len(plain(units[j].text))
        return len(plain(fr[j])) / max(en, 1), en

    flag = set()
    for e in rep:
        if e['bead'] in ('1:2', '1:3'):
            r, _ = ratio(e['nps'][0])
            if 0.7 <= r <= 2.0:
                continue
        if e['bead'] != '1:1':
            flag.update(e['nps'])
            if e.get('attach_to') is not None:
                flag.add(e['attach_to'])
    for j in range(len(units)):
        r, en = ratio(j)
        if (en > 25 and (r < 0.5 or r > 2.4)) or not fr[j]:
            flag.add(j)
    flag = {j for j in flag if not is_gibberish(plain(units[j].text)) and keys[j] not in done}

    groups, cur = [], []
    for j in sorted(flag):
        if cur and j - cur[-1] > 2:
            groups.append(cur)
            cur = []
        cur.append(j)
    if cur:
        groups.append(cur)

    with open(out_path, 'w', encoding='utf-8') as out:
        for g in groups:
            lo, hi = max(0, g[0] - 1), min(len(units) - 1, g[-1] + 1)
            out.write(f'#### {keys[g[0]]}\n')
            o_idx = sorted({i for j in range(lo, hi + 1) for i in src[j]})
            if o_idx:
                o_idx = list(range(o_idx[0], o_idx[-1] + 1))
            for j in range(lo, hi + 1):
                mark = '*' if j in flag else ' '
                lines = ','.join(str(ons[i].line) for i in src[j]) or '-'
                out.write(f'{mark}EN {keys[j]} [{lines}] | {plain(units[j].text)}\n')
            for i in o_idx:
                out.write(f' FR ons:{ons[i].line} | {plain(ons[i].text)}\n')
            out.write('\n')
    print(f'{len(groups)} groupes, {len(flag)} unités signalées')


if __name__ == '__main__':
    main()
