"""Estime le nombre de lignes affichées par page NVL (BOX9) pour détecter les débordements.

usage : python pagecheck.py <police.ttf> <dossier_nps> [max_lignes]
Modèle (voir TEXTBOX_LAYOUT.md) : zone de texte 1104 px de large, pas de ligne 49 px,
16 lignes max ; retour à la ligne par mots ; une ligne source vide = nouvelle page.
"""
import glob
import os
import re
import sys

from PIL import ImageFont

TAG_RE = re.compile(r'<[^<>]*>')
WRAP_W = 1104


def wrap_count(font, text):
    if not text.strip():
        return 1
    lines, cur = 1, ''
    for word in re.split(r'(?<= )', text):
        trial = cur + word
        if font.getlength(trial.rstrip()) <= WRAP_W:
            cur = trial
        else:
            lines += 1
            cur = word
    return lines


def pages(font, content):
    """Génère (ligne_source_début, nb_lignes, [(n° de ligne, nb_lignes affichées), ...]) par page."""
    used, start, rows = 0, None, []
    for n, raw in enumerate(content.split('\n'), 1):
        low = raw.lower()
        if raw.lstrip().startswith('//'):
            continue
        if '<clear>' in low or re.search(r'<box\s', low):
            if rows:
                yield start, used, rows
            used, start, rows = 0, None, []
            if TAG_RE.sub('', raw).split('//')[0].strip() == '':
                continue
        plain = TAG_RE.sub('', raw)
        if raw.lstrip().startswith('<') and not plain.split('//')[0].strip():
            continue
        if not plain.strip():
            # ligne vide = fin de page (attente de clic + effacement), comme « \ » en ONS
            if rows:
                yield start, used, rows
            used, start, rows = 0, None, []
            continue
        if start is None:
            start = n
        c = wrap_count(font, plain)
        rows.append((n, c))
        used += c
    if rows:
        yield start, used, rows


def fix_overflow(font, content, limit):
    """Coupe les pages trop longues en insérant une ligne vide (= nouvelle page) après une
    ligne qui se termine déjà par une attente de clic <K> (retirée, la page vide attend déjà).
    Retourne (contenu, nombre de coupures)."""
    cuts = 0
    while True:
        lines = content.split('\n')
        target = None
        for start, used, rows in pages(font, content):
            if used > limit:
                target = rows
                break
        if target is None:
            return content, cuts
        best, acc = None, 0
        for i, (n, c) in enumerate(target[:-1]):
            acc += c
            if acc > limit:
                break
            if re.search(r'<k>\s*$', lines[n - 1], re.I):
                score = max(acc, sum(x for _, x in target) - acc)
                if best is None or score <= best[0]:
                    best = (score, n)
        if best is None:
            raise ValueError(f'page ligne {target[0][0]} : aucun point de coupure possible')
        n = best[1]
        lines[n - 1] = re.sub(r'<k>\s*$', '', lines[n - 1], flags=re.I)
        lines.insert(n, '')
        content = '\n'.join(lines)
        cuts += 1


def main():
    font = ImageFont.truetype(sys.argv[1], 32)
    folder = sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 16
    worst = []
    for p in sorted(glob.glob(os.path.join(folder, 'sy*.nps'))):
        content = open(p, encoding='utf-8-sig').read().replace('\r\n', '\n')
        for start, used, _ in pages(font, content):
            worst.append((used, os.path.basename(p), start))
    worst.sort(reverse=True)
    over = [w for w in worst if w[0] > limit]
    print(f'pages : {len(worst)}   max : {worst[0][0]} lignes   au-delà de {limit} : {len(over)}')
    for w in over[:60]:
        print(f'  {w[0]:3} lignes  {w[1]}:{w[2]}')


if __name__ == '__main__':
    main()
