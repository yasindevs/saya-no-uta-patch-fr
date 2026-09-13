"""Lecture / écriture des archives NPK2 (Nitroplus N4) de The Song of Saya (Steam/GOG).

Format (little-endian) :
  "NPK2" | u32 version(=2) | IV[16] | u32 nb_fichiers | u32 taille_table | table AES | données
Entrée de table :
  u8 0 | u16 len | nom Shift-JIS | u32 taille | sha256[32] | u32 nb_segments
  puis par segment : u64 offset | u32 taille_alignée | u32 taille_compressée | u32 taille_orig
Chaque bloc (table, segments) : AES-256-CBC, même clé, même IV ; segments ≤ 65536 octets,
compressés en deflate brut quand c'est rentable.
"""
import hashlib
import os
import struct
import zlib

from Cryptodome.Cipher import AES

KEY = bytes.fromhex('d0b71f3c4e24cecfddeea91d24b0403229a3e5330d2951826051d6c94af5af54')
SEGMENT = 65536


def _dec(data, iv):
    pad = (16 - len(data) % 16) % 16
    return AES.new(KEY, AES.MODE_CBC, iv).decrypt(data + b'\0' * pad)


def _enc(data, iv):
    pad = (16 - len(data) % 16) % 16
    return AES.new(KEY, AES.MODE_CBC, iv).encrypt(data + b'\0' * pad)


def read_npk(path):
    """Retourne {nom_virtuel: contenu}."""
    raw = open(path, 'rb').read()
    if raw[:4] != b'NPK2':
        raise ValueError(f'{path} : pas une archive NPK2')
    iv = raw[8:24]
    count, table_size = struct.unpack_from('<II', raw, 24)
    t = _dec(raw[32:32 + table_size], iv)
    pos, files = 0, {}
    for _ in range(count):
        pos += 1
        (nlen,) = struct.unpack_from('<H', t, pos)
        pos += 2
        name = t[pos:pos + nlen].decode('shift-jis')
        pos += nlen + 36
        (nseg,) = struct.unpack_from('<I', t, pos)
        pos += 4
        chunks = []
        for _ in range(nseg):
            off, sal, sc, so = struct.unpack_from('<QIII', t, pos)
            pos += 20
            d = _dec(raw[off:off + sal], iv)[:sc]
            chunks.append(zlib.decompress(d, -15) if sc != so else d)
        files[name] = b''.join(chunks)
    return files


def write_npk(path, files, iv=None):
    """files : {nom_virtuel: bytes}. Écrit une archive NPK2 lisible par le moteur."""
    iv = iv or os.urandom(16)
    names = sorted(files)
    blobs = []      # par fichier : liste de (chiffré, alignée, comp, orig)
    for name in names:
        data = files[name]
        segs = []
        for i in range(0, max(len(data), 1), SEGMENT):
            chunk = data[i:i + SEGMENT]
            co = zlib.compressobj(9, zlib.DEFLATED, -15)
            comp = co.compress(chunk) + co.flush()
            if len(comp) >= len(chunk):
                comp = chunk
            e = _enc(comp, iv)
            segs.append((e, len(e), len(comp), len(chunk)))
        blobs.append(segs)

    def table(offsets):
        out = bytearray()
        for name, segs, offs in zip(names, blobs, offsets):
            nb = name.encode('shift-jis')
            data = files[name]
            out += b'\0' + struct.pack('<H', len(nb)) + nb
            out += struct.pack('<I', len(data)) + hashlib.sha256(data).digest()
            out += struct.pack('<I', len(segs))
            for (_, sal, sc, so), off in zip(segs, offs):
                out += struct.pack('<QIII', off, sal, sc, so)
        return bytes(out)

    zero = [[0] * len(s) for s in blobs]
    table_len = len(_enc(table(zero), iv))
    cur = 32 + table_len
    offsets = []
    for segs in blobs:
        o = []
        for s in segs:
            o.append(cur)
            cur += s[1]
        offsets.append(o)
    etable = _enc(table(offsets), iv)
    with open(path, 'wb') as f:
        f.write(b'NPK2' + struct.pack('<I', 2) + iv + struct.pack('<II', len(names), len(etable)))
        f.write(etable)
        for segs in blobs:
            for s in segs:
                f.write(s[0])


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 4 and sys.argv[1] == 'x':
        for n, d in read_npk(sys.argv[2]).items():
            dest = os.path.join(sys.argv[3], n.replace('/', os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, 'wb').write(d)
            print(n, len(d))
    else:
        print('usage : python npk2.py x <archive.npk> <dossier>')
