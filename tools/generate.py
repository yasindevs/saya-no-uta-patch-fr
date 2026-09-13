"""Génère les .nps français à partir des .nps anglais d'origine + de l'alignement.

usage : python generate.py <dossier_nps_original> <fr_units.json> <overrides.json> <dossier_sortie> <01.utf>
                           [--font droidserif-regular.ttf] [--max-lines 14]

Avec --font, les pages NVL trop longues pour la boîte de texte sont coupées en deux.

overrides.json :
  "units"   : {"sy010.nps:93:0": "texte FR", ...}   — {ons:N} = ligne N de 01.utf
  "ok"      : [clés relues et correctes telles quelles]  (utilisé par review.py)
  "choices" : {"sy100sl.nps": {"texte EN": "texte FR"}}  — attributs TEXT="" des choix
  "raw"     : {"menu.nps": {"motif exact": "remplacement"}}
"""
import argparse
import glob
import json
import os
import random
import re
import sys

from PIL import ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from formats import parse_nps, parse_ons, render_nps, TAG_RE  # noqa: E402
from pagecheck import fix_overflow  # noqa: E402

ITALIC_RE = re.compile(r'</?i>', re.I)
QUOTE_RE = re.compile(r'"[^"]*"?')


def is_gibberish(en_plain):
    """Niveau 1 de la distorsion : charabia plein de symboles (on garde celui de la VO)."""
    q = ''.join(QUOTE_RE.findall(en_plain)) or en_plain
    sym = sum(1 for c in q if c in '#$%^&*@~+=|' or c.isdigit())
    return len(q) > 3 and sym / len(q) > 0.06


def is_random_case(en_plain):
    """Niveau 2 : casse aléatoire lettre par lettre dans les répliques."""
    q = ''.join(QUOTE_RE.findall(en_plain))
    words = re.findall(r"[A-Za-z']{2,}", q)
    if len(words) < 2:
        return False
    odd = sum(1 for w in words if re.search(r'[a-z][A-Z]', w))
    return (odd >= 2 and odd / len(words) > 0.25) or (odd >= 1 and odd / len(words) >= 0.5)


def randomize_case(text, seed):
    """Applique la casse aléatoire aux seules parties entre guillemets (hors balises)."""
    rng = random.Random(seed)
    out, inq = [], False
    for piece in re.split(r'(<[^<>]*>)', text):
        if piece.startswith('<'):
            out.append(piece)
            continue
        buf = []
        for ch in piece:
            if ch == '"':
                inq = not inq
                buf.append(ch)
            elif inq and ch.isalpha():
                buf.append(ch.upper() if rng.random() < 0.5 else ch.lower())
            else:
                buf.append(ch)
        out.append(''.join(buf))
    return ''.join(out)


def clean_fr(s):
    s = s.strip()
    s = re.sub(r'^"\s+', '"', s)            # ^" Hé, ...  ->  "Hé, ...
    s = re.sub(r'\s+"$', '"', s)
    # caractères absents de Droid Serif (voir glyphcheck.py)
    s = s.replace('～', '~').replace('　', ' ')
    s = re.sub(r' {2,}', ' ', s)
    s = s.replace('――', '―')
    return s


def transplant_tags(en_text, fr_text):
    """Recopie dans le FR les balises inline non italiques du texte EN (<se>, </center>…),
    à la même position relative (début, fin, ou proportionnelle sur une frontière de mot)."""
    en_plain_len = len(TAG_RE.sub('', en_text))
    inserts = []
    pos = 0
    for m in re.finditer(r'<[^<>]*>|[^<]+', en_text):
        tok = m.group(0)
        if tok.startswith('<'):
            if not ITALIC_RE.fullmatch(tok):
                inserts.append((pos, tok))
        else:
            pos += len(tok)
    if not inserts:
        return fr_text
    fr_plain = TAG_RE.sub('', fr_text)
    head, tail, mid = [], [], []
    for p, tok in inserts:
        if p == 0:
            head.append(tok)
        elif p >= en_plain_len:
            tail.append(tok)
        else:
            mid.append((p / en_plain_len, tok))
    res = fr_text
    for ratio, tok in sorted(mid, reverse=True):
        target = int(len(fr_plain) * ratio)
        # position en caractères « visibles » -> index dans res (qui peut contenir <I>)
        spaces = [m.start() for m in re.finditer(r' ', fr_plain)]
        if spaces:
            target = min(spaces, key=lambda s: abs(s - target)) + 1
        vis, idx = 0, 0
        while idx < len(res) and vis < target:
            if res[idx] == '<':
                idx = res.index('>', idx) + 1
                continue
            vis += 1
            idx += 1
        res = res[:idx] + tok + res[idx:]
    return ''.join(head) + res + ''.join(tail)


def split_last_word(text):
    """'abc def "ghi"' -> ('abc def ', '"ghi"') ; ignore les espaces à l'intérieur des balises."""
    depth, cut = 0, -1
    for i, ch in enumerate(text.rstrip()):
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth -= 1
        elif ch == ' ' and depth == 0:
            cut = i
    if cut < 0:
        return text, ''
    return text[:cut + 1], text[cut + 1:]


def translate_unit(u, fr, key, manual=False):
    """manual=True : texte relu à la main (overrides), utilisé tel quel hors balises inline."""
    en_plain = TAG_RE.sub('', u.text)
    t = clean_fr(fr)
    if is_gibberish(en_plain) and not manual:
        # charabia de niveau 1 : on garde la VO ; si la ligne contient aussi de la
        # narration, elle doit être traitée à la main dans overrides.json
        if re.sub(r'"[^"]*"', '', en_plain).strip(' ,.'):
            print('  [charabia + narration, à corriger à la main]', key)
        return u.text
    if is_random_case(en_plain) and not is_gibberish(en_plain):
        t = randomize_case(t, key)
    # pensée intérieure : bloc EN entièrement en italique -> idem en FR
    if re.fullmatch(r'\s*<i>.*</i>\s*', u.text, re.I | re.S) and not ITALIC_RE.search(t):
        t = f'<I>{t}</I>'
    return transplant_tags(u.text, t)


def expand_refs(text, ons_by_line):
    """Remplace {ons:N} par le texte FR de la ligne N de 01.utf."""
    def sub(m):
        u = ons_by_line.get(int(m.group(1)))
        if u is None:
            raise KeyError(f'ligne {m.group(1)} de 01.utf : pas une ligne de texte')
        return u.text.strip()
    return re.sub(r'\{ons:(\d+)\}', sub, text)


def main():
    ap = argparse.ArgumentParser()
    for a in ('nps_dir', 'fr_json', 'overrides_json', 'out_dir', 'ons_path'):
        ap.add_argument(a)
    ap.add_argument('--font')
    ap.add_argument('--max-lines', type=int, default=14)
    args = ap.parse_args()
    nps_dir, fr_json, overrides_json, out_dir, ons_path = (
        args.nps_dir, args.fr_json, args.overrides_json, args.out_dir, args.ons_path)
    font = ImageFont.truetype(args.font, 32) if args.font else None
    fr = json.load(open(fr_json, encoding='utf-8'))
    ons_by_line = {u.line: u for u in parse_ons(open(ons_path, encoding='utf-8-sig').read())}
    if os.path.exists(overrides_json):
        ov = json.load(open(overrides_json, encoding='utf-8'))
        units_ov = {k: expand_refs(v, ons_by_line) for k, v in ov.get('units', {}).items()}
        unknown = set(units_ov) - set(fr)
        if unknown:
            raise KeyError(f'clés inconnues dans overrides.json : {sorted(unknown)}')
        manual_keys = set(units_ov)
        fr.update(units_ov)
        choices = ov.get('choices', {})
        raw_replace = ov.get('raw', {})
    else:
        choices, raw_replace, manual_keys = {}, {}, set()
    os.makedirs(out_dir, exist_ok=True)
    missing = total_cuts = 0
    for path in sorted(glob.glob(os.path.join(nps_dir, '*.nps'))):
        name = os.path.basename(path)
        content = open(path, encoding='utf-8-sig').read().replace('\r\n', '\n')
        lines = parse_nps(content, name)
        head = None
        for ln in lines:
            k = 0
            for u in ln.units:
                if u.empty:
                    continue
                key = f'{name}:{u.line}:{k}'
                k += 1
                if u.cont:
                    # phrase coupée sur deux lignes dans la VO : on reproduit la coupure
                    # en laissant le dernier mot du FR sur la seconde ligne
                    if head is not None:
                        head.text, u.text = split_last_word(head.text)
                    continue
                head = None
                t = fr.get(key)
                if t is None:
                    if name.startswith('sy'):
                        missing += 1
                        print('  [EN conservé]', key, u.plain.strip()[:60])
                    continue
                u.text = translate_unit(u, t, key, key in manual_keys)
                head = u
        out = render_nps(lines)
        for en, fr_txt in choices.get(name, {}).items():
            assert f'TEXT="{en}"' in out, f'{name} : choix introuvable : {en}'
            out = out.replace(f'TEXT="{en}"', f'TEXT="{fr_txt}"')
        for en, fr_txt in raw_replace.get(name, {}).items():
            assert en in out, f'{name} : motif introuvable : {en[:60]}'
            out = out.replace(en, fr_txt)
        if font and name.startswith('sy'):
            out, cuts = fix_overflow(font, out, args.max_lines)
            total_cuts += cuts
        # fins de ligne CRLF, sans BOM, comme les fichiers d'origine
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(out)
    print(f'{missing} unités restées en anglais, {total_cuts} page(s) trop longue(s) coupée(s)')


if __name__ == '__main__':
    main()
