"""Generuje src/photos.gen.ts z plików assets/photos/<klucz>-<n>.jpg."""
import os, re, collections
root = os.path.join(os.path.dirname(__file__), '..')
files = sorted(f for f in os.listdir(os.path.join(root, 'assets/photos')) if f.endswith('.jpg'))
g = collections.OrderedDict()
for f in files:
    k = re.sub(r'-\d+\.jpg$', '', f); g.setdefault(k, []).append(f)
out = ['// Plik generowany przez scripts/gen-photos.py – nie edytuj ręcznie.', 'export const PHOTO_FILES: Record<string, number[]> = {']
for k, fs in g.items():
    out.append(f"  '{k}': [" + ', '.join(f"require('../assets/photos/{f}')" for f in fs) + '],')
out.append('};')
# Duże wersje (cały kafelek) pokazywane po kliknięciu: małe zdjęcie -> duże
out.append('export const PHOTO_FULL = new Map<number, number>([')
for f in files:
    if os.path.exists(os.path.join(root, 'assets/photos/full', f)):
        out.append(f"  [require('../assets/photos/{f}'), require('../assets/photos/full/{f}')],")
out.append(']);')
# Nazwa pliku dla każdego zdjęcia (reguły w photos.ts: zdjęcie o konkretnej treści tylko dla pasujących kart)
out.append('export const PHOTO_NAMES = new Map<number, string>([')
for f in files:
    out.append(f"  [require('../assets/photos/{f}'), '{f[:-4]}'],")
out.append(']);')
# Podpisy autorów prawdziwych zdjęć (Wikimedia Commons wymaga podpisu przy CC BY / CC BY-SA)
import json as _json
_cp = os.path.join(root, '..', 'photos', 'credits.json')
_cred = _json.load(open(_cp)) if os.path.exists(_cp) else {}
out.append('export const PHOTO_CREDIT = new Map<number, string>([')
for f in files:
    if f[:-4] in _cred:
        out.append(f"  [require('../assets/photos/{f}'), {_json.dumps(_cred[f[:-4]], ensure_ascii=False)}],")
out.append(']);')
open(os.path.join(root, 'src/photos.gen.ts'), 'w').write('\n'.join(out) + '\n')
print(len(files), 'zdjęć,', len(g), 'kluczy')
