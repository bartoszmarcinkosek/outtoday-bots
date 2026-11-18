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
open(os.path.join(root, 'src/photos.gen.ts'), 'w').write('\n'.join(out) + '\n')
print(len(files), 'zdjęć,', len(g), 'kluczy')
