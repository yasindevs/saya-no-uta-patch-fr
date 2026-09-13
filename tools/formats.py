"""Parseurs des deux formats de script de Saya no Uta.

- NPS : scénario de la version Steam/GOG (moteur Nitroplus N4), balises <TAG> + texte.
- ONS : scénario PONScripter de l'ancienne version (patch FR NNUUU), fichier 01.utf.
"""
import re
from dataclasses import dataclass, field

TAG_RE = re.compile(r'<[^<>]*>')
VOICE_SRC_RE = re.compile(r'SRC="([^"]+)"', re.I)
KWAIT_RE = re.compile(r'<k>', re.I)


def voice_key(src):
    """Normalise un identifiant de voix : '4\\000806_2' -> '4/000806_2'."""
    return src.replace('\\', '/').lower()


# ─────────────────────────────── NPS ───────────────────────────────

@dataclass
class NpsUnit:
    """Un bloc de texte entre deux attentes de clic, dans une ligne .nps."""
    prefix: str          # balises avant le texte (voice, se…)
    indent: str          # espaces de tête du texte
    text: str            # texte, balises inline comprises (<I>, <se>)
    suffix: str          # '<K>' / '<k>' ou ''
    voice: str | None
    file: str = ''
    line: int = 0

    @property
    def plain(self):
        return TAG_RE.sub('', self.text)


@dataclass
class NpsLine:
    raw: str
    units: list = field(default_factory=list)   # vide = ligne sans texte


def _line_has_text(line):
    if line.lstrip().startswith('//'):
        return False
    rest = TAG_RE.sub('', line)
    rest = rest.split('//')[0] if line.lstrip().startswith('<') else rest
    return bool(rest.strip())


def parse_nps(content, fname=''):
    out = []
    prev_open = False     # la ligne de texte précédente se termine sans <K>
    for n, line in enumerate(content.split('\n'), 1):
        if not _line_has_text(line):
            out.append(NpsLine(line))
            prev_open = False
            continue
        units = []
        # découpe sur <K>, en gardant le séparateur
        parts = re.split(r'(<k>)', line, flags=re.I)
        chunks = []
        for i in range(0, len(parts), 2):
            body = parts[i]
            suf = parts[i + 1] if i + 1 < len(parts) else ''
            chunks.append((body, suf))
        for body, suf in chunks:
            if not body and not suf:
                continue
            # balises de tête (avant le premier caractère de texte)
            m = re.match(r'((?:<(?!/?i>)[^<>]*>)*)(\s*)(.*)$', body, re.I | re.S)
            prefix, indent, text = m.group(1), m.group(2), m.group(3)
            v = None
            for t in TAG_RE.findall(prefix):
                if t.lower().startswith('<voice'):
                    s = VOICE_SRC_RE.search(t)
                    if s:
                        v = voice_key(s.group(1))
            if not TAG_RE.sub('', text).strip():
                # bloc sans texte (ex. balise seule en fin de ligne) : on le colle au suivant
                units.append(NpsUnit(prefix, indent, text, suf, v, fname, n))
                units[-1].empty = True
                continue
            u = NpsUnit(prefix, indent, text, suf, v, fname, n)
            u.empty = False
            units.append(u)
        # suite d'une phrase coupée par un retour à la ligne de l'éditeur :
        # « ...didn't⏎we?"<K> » — la ligne commence en colonne 0, sans balise
        real = [u for u in units if not u.empty]
        for u in units:
            u.cont = False
        if real and prev_open and not line[:1].isspace() and not line.startswith('<'):
            real[0].cont = True
        prev_open = bool(real) and not units[-1].suffix
        out.append(NpsLine(line, units))
    return out


def render_nps(lines):
    res = []
    for ln in lines:
        if not ln.units:
            res.append(ln.raw)
        else:
            res.append(''.join(u.prefix + u.indent + u.text + u.suffix for u in ln.units))
    return '\n'.join(res)


# ─────────────────────────────── ONS ───────────────────────────────

ONS_COMMANDS = {
    'bg', 'br', 'btnwait', 'cl', 'csp', 'delay', 'dwave', 'dwaveloop', 'dwavestop', 'for',
    'gosub', 'goto', 'if', 'ld', 'lsp', 'mov', 'msp', 'next', 'print', 'reset', 'skipoff',
    'spbtn', 'textoff', 'texton', 'wait', 'mp3stop', 'mp3loop', 'mp3play', 'select', 'return',
    'add', 'inc', 'dec', 'end', 'click', 'lookbackflush', 'mpegplay', 'quake', 'monocro',
    'nega', 'setwindow3', 'setcursor', 'saveon', 'saveoff', 'erasetextwindow', 'bgcopy',
    'automode', 'systemcall', 'rmode', 'textclear', 'wavestop', 'waveloop', 'wave', 'jumpf',
    'jumpb', 'cmp', 'itoa', 'len', 'mid', 'getparam', 'defsub', 'resettimer', 'waittimer',
    'vsp', 'amsp', 'bar', 'barclear', 'play', 'stop', 'loopbgm', 'loopbgmstop', 'chvol',
}
ONS_VOICE_RE = re.compile(r'dwave\s+0\s*,\s*"voice\\([^"]+?)\.ogg"', re.I)


@dataclass
class OnsUnit:
    text: str            # texte converti (italique -> <I>, sans ^ ni terminateur)
    term: str            # '@', '\\', '/', ''
    voice: str | None
    label: str
    line: int


def _is_ons_command(line):
    m = re.match(r'\s*([a-z_][a-z0-9_]*)', line)
    return bool(m) and m.group(1) in ONS_COMMANDS


def ons_text_to_nps(s):
    """Convertit le balisage PONScripter en balisage NPS."""
    s = s.replace('^', '')
    out, italic = [], False
    for piece in re.split(r'(~i~)', s):
        if piece == '~i~':
            out.append('</I>' if italic else '<I>')
            italic = not italic
        else:
            out.append(piece)
    if italic:
        out.append('</I>')
    s = ''.join(out)
    s = s.replace('――', '―')
    return s


def parse_ons(content):
    lines = content.replace('\r\n', '\n').split('\n')
    units, voice, label = [], None, ''
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.startswith(';'):
            continue
        if line.startswith('*'):
            label = line.strip()
            voice = None
            continue
        if _is_ons_command(line):
            m = ONS_VOICE_RE.search(line)
            if m:
                voice = voice_key(m.group(1))
            continue
        body = line.rstrip()
        if body.lstrip('^').startswith(('※ DEBUG', '＜＜')):
            continue    # message de debug / commentaire japonais laissé dans le script
        term = ''
        if body.endswith('@/'):
            term, body = '@/', body[:-2]
        elif body[-1:] in ('@', '\\', '/'):
            term, body = body[-1], body[:-1]
        prev = units[-1] if units else None
        if prev and prev.term.endswith('/') and voice is None and prev.label == label:
            # « …qu'elle ne s'y attendait,@/ » + bruitage + « elle le pousse… » : même phrase,
            # coupée pour caler un son. On recolle (le NPS garde un seul bloc avec <se> inline).
            prev.text = prev.text.rstrip() + ' ' + ons_text_to_nps(body).lstrip()
            prev.term = term
        else:
            units.append(OnsUnit(ons_text_to_nps(body), term, voice, label, n))
        voice = None
    return units
