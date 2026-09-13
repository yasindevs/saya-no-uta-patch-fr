"""Dessine la bannière du patch (README + installateur), sans aucun visuel du jeu.

usage : python make_banner.py <droidserif-regular.ttf>
Sorties : banner.png (1280×420), banner_installer.png (720×200), icon.ico
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
KANJI_FONTS = [r'C:\Windows\Fonts\YuGothL.ttc', r'C:\Windows\Fonts\YuGothR.ttc', r'C:\Windows\Fonts\msgothic.ttc']


def radial(size, center, radius, color, alpha):
    w, h = size
    layer = Image.new('RGBA', size, color + (0,))
    mask = Image.new('L', size, 0)
    d = ImageDraw.Draw(mask)
    steps = 60
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(alpha * (1 - i / steps) ** 1.6)
        d.ellipse([center[0] - r, center[1] - r * 0.7, center[0] + r, center[1] + r * 0.7], fill=a)
    layer.putalpha(mask.filter(ImageFilter.GaussianBlur(radius / 8)))
    return layer


def bezier(p0, p1, p2, p3, n=80):
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        yield (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
               u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]), t


def tendrils(size, rng, count, scale):
    w, h = size
    layer = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    palette = [(46, 94, 60), (70, 120, 78), (110, 28, 38), (140, 44, 52), (38, 70, 48)]
    for _ in range(count):
        side = rng.choice(['left', 'right', 'bottom', 'top'])
        if side == 'left':
            p0 = (-20, rng.uniform(0, h))
        elif side == 'right':
            p0 = (w + 20, rng.uniform(0, h))
        elif side == 'bottom':
            p0 = (rng.uniform(0, w), h + 20)
        else:
            p0 = (rng.uniform(0, w), -20)
        # les lianes restent sur les bords pour laisser le centre lisible
        tx = rng.uniform(0.05, 0.32) * w if p0[0] < w / 2 else rng.uniform(0.68, 0.95) * w
        p3 = (tx, rng.uniform(0.1, 0.9) * h)
        p1 = (p0[0] + rng.uniform(-200, 200) * scale, p0[1] + rng.uniform(-160, 160) * scale)
        p2 = (p3[0] + rng.uniform(-220, 220) * scale, p3[1] + rng.uniform(-180, 180) * scale)
        color = rng.choice(palette)
        width = rng.uniform(2.5, 9) * scale
        alpha = rng.randint(70, 150)
        prev = None
        for (x, y), t in bezier(p0, p1, p2, p3):
            r = max(0.6, width * (1 - t) ** 1.2)
            if prev:
                d.line([prev, (x, y)], fill=color + (alpha,), width=int(r * 2))
            d.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
            prev = (x, y)
        # petite vrille au bout
        cx, cy = p3
        a0 = rng.uniform(0, math.tau)
        for k in range(24):
            ang = a0 + k * 0.35
            rr = (24 - k) * 0.9 * scale
            d.ellipse([cx + math.cos(ang) * rr - 1, cy + math.sin(ang) * rr - 1,
                       cx + math.cos(ang) * rr + 1, cy + math.sin(ang) * rr + 1], fill=color + (alpha,))
    glow = layer.filter(ImageFilter.GaussianBlur(6 * scale))
    return Image.alpha_composite(glow, layer)


def grain(size, rng, strength):
    noise = Image.effect_noise(size, 40).convert('L')
    noise = noise.point(lambda v: 128 + (v - 128) * strength)
    return Image.merge('RGB', (noise, noise, noise))


def banner(size, font_path, seed=7, compact=False):
    w, h = size
    scale = w / 1280
    rng = random.Random(seed)
    img = Image.new('RGBA', size, (11, 8, 9, 255))
    img = Image.alpha_composite(img, radial(size, (w * 0.18, h * 0.55), w * 0.42, (120, 18, 30), 150))
    img = Image.alpha_composite(img, radial(size, (w * 0.86, h * 0.35), w * 0.38, (30, 96, 60), 120))
    img = Image.alpha_composite(img, tendrils(size, rng, 38 if not compact else 26, scale))

    # voile central pour la lisibilité du titre
    img = Image.alpha_composite(img, radial(size, (w * 0.5, h * 0.5), w * 0.45, (8, 6, 7), 210))

    d = ImageDraw.Draw(img)
    kanji_font = next((f for f in KANJI_FONTS if os.path.exists(f)), None)
    if kanji_font:
        kf = ImageFont.truetype(kanji_font, int(h * 0.62))
        k = Image.new('RGBA', size, (0, 0, 0, 0))
        kd = ImageDraw.Draw(k)
        kd.text((w * 0.5, h * 0.5), '沙耶の唄', font=kf, anchor='mm', fill=(160, 40, 52, 34))
        img = Image.alpha_composite(img, k)
        d = ImageDraw.Draw(img)

    title = ImageFont.truetype(font_path, int(h * (0.26 if not compact else 0.27)))
    sub = ImageFont.truetype(font_path, int(h * (0.085 if not compact else 0.095)))
    small = ImageFont.truetype(font_path, int(h * (0.055 if not compact else 0.068)))
    ty = h * (0.40 if not compact else 0.38)
    # halo sombre autour des glyphes, façon FONT_SHADOW_TYPE_AROUND du moteur
    halo = Image.new('RGBA', size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).text((w / 2, ty), 'Saya no Uta', font=title, anchor='mm', fill=(0, 0, 0, 230))
    img = Image.alpha_composite(img, halo.filter(ImageFilter.GaussianBlur(5 * scale)))
    d = ImageDraw.Draw(img)
    d.text((w / 2, ty), 'Saya no Uta', font=title, anchor='mm', fill=(236, 229, 222, 255))
    line_y = ty + h * 0.17
    d.line([(w / 2 - w * 0.17, line_y), (w / 2 + w * 0.17, line_y)], fill=(150, 30, 44, 255), width=max(1, int(2 * scale)))
    d.text((w / 2, line_y + h * 0.09), 'Patch de traduction française · Steam / GOG', font=sub, anchor='mm',
           fill=(206, 190, 182, 255))
    if not compact:
        d.text((w / 2, line_y + h * 0.20), 'Traduction NNUUU Production  ―  Portage yasindevs', font=small,
               anchor='mm', fill=(150, 134, 128, 255))

    rgb = img.convert('RGB')
    rgb = ImageChops.overlay(rgb, grain(size, rng, 0.35))
    return rgb


def icon(font_path):
    s = 256
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, s - 8, s - 8], radius=46, fill=(16, 10, 12, 255), outline=(150, 30, 44, 255), width=6)
    f = ImageFont.truetype(font_path, 150)
    d.text((s / 2, s / 2 - 6), 'S', font=f, anchor='mm', fill=(236, 229, 222, 255))
    d.line([(70, 200), (186, 200)], fill=(70, 130, 88, 255), width=6)
    img.save(os.path.join(HERE, 'icon.ico'), sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])


def main():
    font_path = sys.argv[1]
    banner((1280, 420), font_path).save(os.path.join(HERE, 'banner.png'), optimize=True)
    banner((720, 200), font_path, seed=11, compact=True).save(os.path.join(HERE, 'banner_installer.png'), optimize=True)
    icon(font_path)
    print('ok')


if __name__ == '__main__':
    main()
