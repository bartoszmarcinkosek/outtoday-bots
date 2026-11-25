# Zasady jakości źródeł (stałe reguły, decyzja właściciela 25.11.2026)

Wszystkie reguły działają same, bez AI i bez kosztów.

1. **Ocena źródeł** – `bot/run.py` (`DB.probation`, `DB._guard`). Źródło, z którego przy kontroli odrzucono
   co najmniej 40% ocenionych pozycji (minimum 5 ocenionych), traci automatyczne zatwierdzanie: jego nowe
   pozycje czekają na przegląd. Liczone na bieżąco z bazy; źródło wraca samo, gdy jego pozycje znów przechodzą.
   Dotyczy wszystkich botów (strony, Instagram, hotele, newslettery). Ręczne wpisy (`manual/`) nie są wstrzymywane.
   Podgląd listy: diag.yml ze skryptem `diag_source_health` (linie `SP|`).
2. **Konta Instagram uśpione** – `bot/instagram.py`, stan w `audit/ig_state.json`. Konto czytane raz w tygodniu
   (poniedziałek) zamiast codziennie, gdy: jego najnowszy post ma ponad 30 dni, albo jest na liście ≥ 60 dni
   i przez 60 dni nie dało żadnego wydarzenia ani oferty.
3. **Strony blokujące roboty** – bot już czyta strony prawdziwą przeglądarką i szanuje robots.txt; blokad nie
   obchodzimy. Źródło blokowane (403, robots.txt) musi mieć zastępstwo: oficjalne konto Instagram tej instytucji
   w `sources/instagram.json`. Pilnuje tego cotygodniowe zadanie „OutToday – źródła blokowane i martwe”
   (lista: `diag_source_health`, linie `SB|`). Nazw kont nie zgadujemy – tylko ze strony oficjalnej.
4. **Pierwszeństwo organizatora** – `bot/run.py`. Gdy wydarzenie jest w apce ze sprzedawcy biletów lub portalu,
   a potem podaje je sam organizator, link w apce przechodzi na stronę organizatora (link do biletów zostaje),
   a puste pola (godzina, cena) uzupełniają się z jego strony.
5. **Dane bez AI** – `bot/run.py` (`structured_events`, `apply_structured`). Gdy strona podaje wydarzenia jako
   dane strukturalne (JSON-LD), data i godzina pochodzą stamtąd, nie z odczytu AI. Pomiar 25.11.2026: takie dane
   ma 17 ze 133 źródeł (diag.yml, skrypt `diag_structured`). Kategorię i opis nadal ustala AI.
6. **Martwe źródła** – `bot/source_repair.py`, workflow `source-repair.yml` (sobota). Adres, który zniknął (404)
   albo się przeniósł, bot naprawia sam: bierze nowy adres z przekierowania albo znajduje stronę wydarzeń na
   stronie głównej tej samej domeny. Nigdy nie przyjmuje bloga, strony z minionym rokiem ani adresu innego źródła.
   Czego nie naprawi, wypisuje (linie `RX|`) do decyzji.
