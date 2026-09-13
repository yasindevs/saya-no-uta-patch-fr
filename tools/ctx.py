"""Affiche le contexte d'alignement autour d'une position (outil de relecture).

usage : python ctx.py <dossier_nps_original> <01.utf> <fichier.nps> <ligne_debut> <ligne_fin>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from build_alignment import load_nps  # noqa: E402
from formats import parse_ons, TAG_RE  # noqa: E402
from align import align  # noqa: E402


def main():
    nps_dir, ons_path, fname, a, b = sys.argv[1:6]
    a, b = int(a), int(b)
    units, keys = load_nps(nps_dir)
    ons = parse_ons(open(ons_path, encoding='utf-8-sig').read())
    _, _, _, src = align(units, ons)
    sel = [j for j, u in enumerate(units) if u.file == fname and a <= u.line <= b]
    idx = sorted({i for j in sel for i in src[j]})
    for j in sel:
        print(f'EN {keys[j]} [{",".join(str(ons[i].line) for i in src[j])}] | {TAG_RE.sub("", units[j].text).strip()}')
    if idx:
        for i in range(max(0, idx[0] - 1), min(len(ons), idx[-1] + 2)):
            print(f'FR ons:{ons[i].line} | {TAG_RE.sub("", ons[i].text).strip()}')


if __name__ == '__main__':
    main()
