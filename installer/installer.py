"""Installateur du patch français de The Song of Saya (Steam / GOG).

Le patch n'écrase aucun fichier du jeu : il ajoute <jeu>/patch/saya_fr.npk, que le moteur
charge par-dessus script.npk. Désinstaller = supprimer ce fichier.

usage : SayaNoUta-PatchFR.exe                      (interface graphique)
        SayaNoUta-PatchFR.exe --install   <dossier_du_jeu>
        SayaNoUta-PatchFR.exe --uninstall <dossier_du_jeu>
"""
import ctypes
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys
import webbrowser

REPO_URL = 'https://github.com/yasindevs/saya-no-uta-patch-fr'
PATCH_NAME = 'saya_fr.npk'
GOG_ID = '1541066319'
GAME_EXE = 'Saya_en.exe'

BG = '#0f0b0c'
PANEL = '#1a1315'
FG = '#e6dfd9'
MUTED = '#9c8d87'
ACCENT = '#8e1b2a'
ACCENT_HOVER = '#a8263a'
GREEN = '#4f9a68'


def resource(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    for cand in (os.path.join(base, name), os.path.join(base, '..', 'dist', name),
                 os.path.join(base, '..', 'assets', name)):
        if os.path.exists(cand):
            return os.path.abspath(cand)
    return os.path.join(base, name)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ───────────────────────── détection du jeu ─────────────────────────

def is_game_dir(path):
    return bool(path) and os.path.isfile(os.path.join(path, GAME_EXE)) and \
        os.path.isfile(os.path.join(path, 'script.npk'))


def _reg_value(root, key, value):
    try:
        import winreg
        with winreg.OpenKey(root, key) as k:
            return winreg.QueryValueEx(k, value)[0]
    except OSError:
        return None


def steam_libraries():
    try:
        import winreg
    except ImportError:
        return []
    roots = [_reg_value(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
             _reg_value(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')]
    libs = []
    for root in filter(None, roots):
        libs.append(root)
        vdf = os.path.join(root, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf):
            text = open(vdf, encoding='utf-8', errors='replace').read()
            libs += [p.replace('\\\\', '\\') for p in re.findall(r'"path"\s+"([^"]+)"', text)]
    unique = {}
    for p in libs:
        unique.setdefault(os.path.normcase(os.path.normpath(p)), os.path.normpath(p))
    return list(unique.values())


def find_game_dirs():
    found = []
    try:
        import winreg
        for key in (rf'SOFTWARE\WOW6432Node\GOG.com\Games\{GOG_ID}', rf'SOFTWARE\GOG.com\Games\{GOG_ID}'):
            p = _reg_value(winreg.HKEY_LOCAL_MACHINE, key, 'path')
            if p:
                found.append(p)
    except ImportError:
        pass
    for lib in steam_libraries():
        found += [os.path.dirname(e) for e in glob.glob(os.path.join(lib, 'steamapps', 'common', '*', GAME_EXE))]
    for drive in 'CDEFG':
        found += [rf'{drive}:\GOG Games\The Song of Saya',
                  rf'{drive}:\Program Files (x86)\GOG Galaxy\Games\The Song of Saya',
                  rf'{drive}:\SteamLibrary\steamapps\common\The Song of Saya']
    return [p for p in dict.fromkeys(os.path.normpath(p) for p in found) if is_game_dir(p)]


# ───────────────────────── installation ─────────────────────────

def patch_path(game_dir):
    return os.path.join(game_dir, 'patch', PATCH_NAME)


def status(game_dir):
    """'absent' | 'a_jour' | 'ancien'"""
    p = patch_path(game_dir)
    if not os.path.exists(p):
        return 'absent'
    return 'a_jour' if sha256(p) == sha256(resource(PATCH_NAME)) else 'ancien'


def install(game_dir):
    os.makedirs(os.path.join(game_dir, 'patch'), exist_ok=True)
    shutil.copyfile(resource(PATCH_NAME), patch_path(game_dir))


def uninstall(game_dir):
    p = patch_path(game_dir)
    if os.path.exists(p):
        os.remove(p)
    d = os.path.dirname(p)
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)


def run_elevated(action, game_dir):
    """Relance l'installateur en administrateur (dossier Program Files). Retourne le code de sortie."""
    if getattr(sys, 'frozen', False):
        exe, params = sys.executable, f'{action} "{game_dir}"'
    else:
        exe, params = sys.executable, f'"{os.path.abspath(__file__)}" {action} "{game_dir}"'

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.c_ulong), ('fMask', ctypes.c_ulong), ('hwnd', ctypes.c_void_p),
                    ('lpVerb', ctypes.c_wchar_p), ('lpFile', ctypes.c_wchar_p), ('lpParameters', ctypes.c_wchar_p),
                    ('lpDirectory', ctypes.c_wchar_p), ('nShow', ctypes.c_int), ('hInstApp', ctypes.c_void_p),
                    ('lpIDList', ctypes.c_void_p), ('lpClass', ctypes.c_wchar_p), ('hkeyClass', ctypes.c_void_p),
                    ('dwHotKey', ctypes.c_ulong), ('hIcon', ctypes.c_void_p), ('hProcess', ctypes.c_void_p)]

    info = SHELLEXECUTEINFO(cbSize=ctypes.sizeof(SHELLEXECUTEINFO), fMask=0x40, lpVerb='runas',
                            lpFile=exe, lpParameters=params, nShow=0)
    if not ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(info)):
        return 1223   # UAC refusé
    ctypes.windll.kernel32.WaitForSingleObject(info.hProcess, 0xFFFFFFFF)
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(info.hProcess)
    return code.value


def do_action(action, game_dir):
    """Exécute l'action, en élevant les droits si nécessaire. Lève une exception en cas d'échec."""
    fn = install if action == '--install' else uninstall
    try:
        fn(game_dir)
    except PermissionError:
        code = run_elevated(action, game_dir)
        if code == 1223:
            raise PermissionError('Droits administrateur refusés.')
        if code != 0:
            raise RuntimeError(f"L'opération en mode administrateur a échoué (code {code}).")


# ───────────────────────── interface ─────────────────────────

def gui():
    import tkinter as tk
    from tkinter import filedialog

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass

    root = tk.Tk()
    root.title('Saya no Uta ― Patch FR')
    root.configure(bg=BG)
    root.resizable(False, False)
    try:
        root.iconbitmap(resource('icon.ico'))
    except tk.TclError:
        pass

    banner = tk.PhotoImage(file=resource('banner_installer.png'))
    tk.Label(root, image=banner, bg=BG, bd=0).pack()

    body = tk.Frame(root, bg=BG, padx=26, pady=18)
    body.pack(fill='both')

    font = ('Segoe UI', 10)
    tk.Label(body, text='Dossier du jeu (Steam ou GOG)', bg=BG, fg=MUTED, font=font, anchor='w').pack(fill='x')

    row = tk.Frame(body, bg=BG)
    row.pack(fill='x', pady=(4, 12))
    game_var = tk.StringVar()
    entry = tk.Entry(row, textvariable=game_var, bg=PANEL, fg=FG, insertbackground=FG, relief='flat',
                     font=font, highlightthickness=1, highlightbackground='#3a2a2e', highlightcolor=ACCENT)
    entry.pack(side='left', fill='x', expand=True, ipady=6)

    def button(parent, text, cmd, primary=False):
        b = tk.Button(parent, text=text, command=cmd, relief='flat', bd=0, cursor='hand2',
                      font=('Segoe UI Semibold', 10), padx=16, pady=7,
                      bg=ACCENT if primary else PANEL, fg=FG,
                      activebackground=ACCENT_HOVER if primary else '#2a1f22', activeforeground=FG)
        b.bind('<Enter>', lambda e: b.config(bg=ACCENT_HOVER if primary else '#2a1f22'))
        b.bind('<Leave>', lambda e: b.config(bg=ACCENT if primary else PANEL))
        return b

    def browse():
        d = filedialog.askdirectory(title='Choisis le dossier de The Song of Saya')
        if d:
            game_var.set(os.path.normpath(d))

    button(row, 'Parcourir…', browse).pack(side='left', padx=(8, 0))

    status_var = tk.StringVar()
    status_lbl = tk.Label(body, textvariable=status_var, bg=BG, fg=MUTED, font=font, anchor='w', justify='left')
    status_lbl.pack(fill='x', pady=(0, 14))

    actions = tk.Frame(body, bg=BG)
    actions.pack(fill='x')

    def refresh(*_):
        d = game_var.get().strip()
        if not d:
            status_var.set('Aucun jeu détecté automatiquement : indique le dossier qui contient Saya_en.exe.')
            status_lbl.config(fg=MUTED)
        elif not is_game_dir(d):
            status_var.set('✗ Ce dossier ne contient pas Saya_en.exe et script.npk.')
            status_lbl.config(fg='#d0616f')
        else:
            s = status(d)
            status_var.set({'absent': '● Jeu trouvé ― patch non installé.',
                            'a_jour': '✓ Patch français installé et à jour.',
                            'ancien': '● Une autre version du patch est installée : clique sur Installer pour la mettre à jour.'}[s])
            status_lbl.config(fg=GREEN if s == 'a_jour' else FG)
        ok = is_game_dir(d)
        for b in (install_btn, uninstall_btn, launch_btn):
            b.config(state='normal' if ok else 'disabled')

    def act(action):
        d = game_var.get().strip()
        try:
            do_action(action, d)
        except Exception as e:  # noqa: BLE001 — message affiché à l'utilisateur
            status_var.set(f'✗ {e}')
            status_lbl.config(fg='#d0616f')
            return
        refresh()
        if action == '--uninstall':
            status_var.set('Patch désinstallé : le jeu est revenu en anglais.')

    def launch():
        d = game_var.get().strip()
        subprocess.Popen([os.path.join(d, GAME_EXE)], cwd=d)

    install_btn = button(actions, 'Installer le patch', lambda: act('--install'), primary=True)
    install_btn.pack(side='left')
    uninstall_btn = button(actions, 'Désinstaller', lambda: act('--uninstall'))
    uninstall_btn.pack(side='left', padx=8)
    launch_btn = button(actions, 'Lancer le jeu', launch)
    launch_btn.pack(side='right')

    info = ('Le patch n\'écrase aucun fichier du jeu : il ajoute patch\\saya_fr.npk.\n'
            'Traduction : NNUUU Production (2010) ― Portage Steam / GOG : yasindevs')
    tk.Label(body, text=info, bg=BG, fg=MUTED, font=('Segoe UI', 9), justify='left', anchor='w').pack(fill='x', pady=(18, 4))
    link = tk.Label(body, text=REPO_URL.replace('https://', ''), bg=BG, fg='#c9606e', cursor='hand2',
                    font=('Segoe UI', 9, 'underline'), anchor='w')
    link.pack(fill='x')
    link.bind('<Button-1>', lambda e: webbrowser.open(REPO_URL))

    game_var.trace_add('write', refresh)
    dirs = find_game_dirs()
    if dirs:
        game_var.set(dirs[0])
    refresh()
    root.mainloop()


def main():
    if len(sys.argv) == 3 and sys.argv[1] in ('--install', '--uninstall'):
        game_dir = sys.argv[2]
        if not is_game_dir(game_dir):
            print(f'✗ {game_dir} : Saya_en.exe / script.npk introuvables')
            sys.exit(2)
        (install if sys.argv[1] == '--install' else uninstall)(game_dir)
        print('✓ terminé')
        sys.exit(0)
    gui()


if __name__ == '__main__':
    main()
