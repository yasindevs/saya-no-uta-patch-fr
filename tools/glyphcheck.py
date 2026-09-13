"""Liste les caractères du texte absents de la police du jeu (ils s'afficheraient en carré).

usage : python glyphcheck.py <police.ttf> <dossier_nps>
"""
import collections
import glob
import os
import re
import sys

from PIL import ImageFont

TAG_RE = re.compile(r'<[^<>]*>')


def main():
    font = ImageFont.truetype(sys.argv[1], 32)

    def sig(c):
        m = font.getmask(c)
        return m.size, bytes(m)

    notdef = sig('')
    count, where = collections.Counter(), {}
    for path in sorted(glob.glob(os.path.join(sys.argv[2], '*.nps'))):
        name = os.path.basename(path)
        for n, line in enumerate(open(path, encoding='utf-8'), 1):
            if line.lstrip().startswith('//'):
                continue
            text = TAG_RE.sub('', line)
            if line.lstrip().startswith('<'):
                text = text.split('//')[0]
            for ch in text:
                if ord(ch) > 0x7e:
                    count[ch] += 1
                    where.setdefault(ch, f'{name}:{n}')
    bad = [c for c in count if sig(c) == notdef]
    print('caractères non ASCII :', ''.join(sorted(count)))
    for c in bad:
        print(f'  ABSENT {c!r} U+{ord(c):04X} ×{count[c]} (ex. {where[c]})')
    print(f'{len(bad)} caractère(s) absent(s)')


if __name__ == '__main__':
    main()
