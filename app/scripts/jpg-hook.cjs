// Poza telefonem zdjęcie to po prostu ścieżka pliku (żeby dało się sprawdzić, które zdjęcie dostaje karta).
require.extensions['.jpg'] = (m, f) => { m.exports = f; };
require.extensions['.png'] = (m, f) => { m.exports = f; };
