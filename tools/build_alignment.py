"""Construit l'alignement EN (.nps) ↔ FR (01.utf) et écrit un rapport de relecture.

usage : python build_alignment.py <dossier_nps_original> <01.utf> <sortie.json> [rapport.txt]
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from formats import parse_nps, parse_ons, TAG_RE  # noqa: E402
from align import align  # noqa: E402


def unit_key(u, k):
    return f'{u.file}:{u.line}:{k}'


def load_nps(nps_dir):
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(nps_dir, 'sy*.nps')))
    units, keys = [], []
    for name in files:
        content = open(os.path.join(nps_dir, name), encoding='utf-8-sig').read().replace('\r\n', '\n')
        for ln in parse_nps(content, name):
            k = 0
            for u in ln.units:
                if u.empty:
                    continue
                if u.cont and units:
                    # la suite d'une phrase coupée est fusionnée avec son début pour l'alignement
                    units[-1].text = units[-1].text.rstrip() + ' ' + u.text
                    units[-1].suffix = u.suffix
                else:
                    units.append(u)
                    keys.append(unit_key(u, k))
                k += 1
    return units, keys


def main():
    nps_dir, ons_path, out_json = sys.argv[1:4]
    report_path = sys.argv[4] if len(sys.argv) > 4 else None
    units, keys = load_nps(nps_dir)
    ons = parse_ons(open(ons_path, encoding='utf-8-sig').read())
    fr, report, anchors, src = align(units, ons)

    data = {k: (t.strip() if t is not None else None) for k, t in zip(keys, fr)}
    json.dump(data, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    missing = [k for k, t in data.items() if not t]
    print(f'unités NPS : {len(units)}   unités FR : {len(ons)}   ancres voix : {len(anchors) - 2}')
    print(f'perles non 1:1 : {len(report)}   unités sans texte FR : {len(missing)}')

    if report_path:
        with open(report_path, 'w', encoding='utf-8') as f:
            for e in report:
                f.write(f"==== {e['bead']}  {keys[e['nps'][0]] if e['nps'] else 'attach->' + str(keys[e['attach_to']] if e.get('attach_to') is not None else None)}"
                        f"  {('split=' + e['split']) if 'split' in e else ''}\n")
                for a in e['nps']:
                    f.write(f"  EN [{keys[a]}] {TAG_RE.sub('', units[a].text).strip()}\n")
                for b in e['ons']:
                    f.write(f"  FR [ons:{ons[b].line}] {ons[b].text.strip()}\n")
                for a in e['nps']:
                    f.write(f"  => [{keys[a]}] {data[keys[a]]}\n")
                f.write('\n')


if __name__ == '__main__':
    main()
