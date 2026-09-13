"""Construit l'archive du patch FR (patch/saya_fr.npk) à partir de ta copie du jeu.

usage :
  python build.py --game "C:/GOG Games/The Song of Saya" --ons "chemin/vers/01.utf"
                  [--script-npk script.npk_original] [--out dist/saya_fr.npk]

- --game       : dossier du jeu Steam/GOG (Saya_en.exe, script.npk, font.npk)
- --ons        : 01.utf de l'ancienne version PONScripter patchée par NNUUU Production
- --script-npk : script.npk d'origine, si celui du jeu a déjà été modifié

Dépendances : pip install pycryptodomex pillow
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, 'tools')
sys.path.insert(0, TOOLS)
from npk2 import read_npk, write_npk  # noqa: E402

ONS_SHA256 = '3033bb54169d779d76ed1df2d47847a351f89852a6ee1f6804d2311223ade7da'


def run(*args):
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    subprocess.run([sys.executable, *args], check=True, env=env)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--game', required=True)
    ap.add_argument('--ons', required=True)
    ap.add_argument('--script-npk')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist', 'saya_fr.npk'))
    ap.add_argument('--keep-temp', action='store_true')
    args = ap.parse_args()

    ons_hash = hashlib.sha256(open(args.ons, 'rb').read()).hexdigest()
    if ons_hash != ONS_SHA256:
        print(f'⚠ 01.utf différent de la version de référence ({ons_hash[:12]}…) : '
              'les corrections manuelles risquent de ne plus tomber juste.')

    script_npk = args.script_npk or os.path.join(args.game, 'script.npk')
    print(f'[1/5] Lecture de {script_npk}')
    script = read_npk(script_npk)
    expected = json.load(open(os.path.join(ROOT, 'data', 'script_npk_sha256.json')))
    bad = [n for n, h in expected.items() if hashlib.sha256(script.get(n, b'')).hexdigest() != h]
    if bad:
        sys.exit(f'✗ script.npk modifié ({len(bad)} fichier(s) : {", ".join(os.path.basename(b) for b in bad[:5])}). '
                 'Passe le script.npk d\'origine avec --script-npk.')

    tmp = tempfile.mkdtemp(prefix='saya_fr_')
    try:
        nps_dir = os.path.join(tmp, 'nps_en')
        os.makedirs(nps_dir)
        for name, data in script.items():
            if name.startswith('media/script/nps/'):
                open(os.path.join(nps_dir, os.path.basename(name)), 'wb').write(data)
        font_path = os.path.join(tmp, 'droidserif-regular.ttf')
        font = [d for n, d in read_npk(os.path.join(args.game, 'font.npk')).items() if n.endswith('.ttf')][0]
        open(font_path, 'wb').write(font)

        print('[2/5] Alignement EN ↔ FR')
        fr_json = os.path.join(tmp, 'fr_units.json')
        run(os.path.join(TOOLS, 'build_alignment.py'), nps_dir, args.ons, fr_json)

        print('[3/5] Génération des scripts FR')
        out_nps = os.path.join(tmp, 'nps_fr')
        run(os.path.join(TOOLS, 'generate.py'), nps_dir, fr_json, os.path.join(ROOT, 'data', 'overrides.json'),
            out_nps, args.ons, '--font', font_path, '--max-lines', '14')

        print('[4/5] Vérifications')
        run(os.path.join(TOOLS, 'pagecheck.py'), font_path, out_nps, '14')
        run(os.path.join(TOOLS, 'glyphcheck.py'), font_path, out_nps)

        print('[5/5] Écriture de l\'archive')
        files = {}
        for name in sorted(os.listdir(out_nps)):
            new = open(os.path.join(out_nps, name), 'rb').read()
            if new != script[f'media/script/nps/{name}']:
                files[f'media/script/nps/{name}'] = new
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        write_npk(args.out, files)
        print(f'✓ {args.out} : {len(files)} scripts, {os.path.getsize(args.out):,} octets')
        print(f'  À copier dans : {os.path.join(args.game, "patch")}')
    finally:
        if args.keep_temp:
            print('fichiers temporaires :', tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
