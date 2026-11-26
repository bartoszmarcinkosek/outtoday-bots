# Zasady jakości źródeł (stałe reguły, decyzja właściciela 25.11.2026)

Wszystkie reguły działają same, bez AI i bez kosztów (8 reguł, stan 26.11.2026).

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
7. **Kontrola jakości po każdym wyszukiwaniu** (decyzja właściciela 26.11.2026) – `bot/qa_after_add.py`.
   **Bramka (26.11.2026, „cokolwiek jest wstawiane musi od razu przejść kontrolę jakości”):** nowa pozycja z bota lub pliku manual/ trafia do bazy jako `pending` (niewidoczna) i staje się `approved` dopiero, gdy przejdzie kontrolę (`QA|PASSED`); nie przeszła → zostaje ukryta (`QA|HELD`). Kod: `DB.insert` w bot/run.py (lista QA_GATE_WORKFLOWS, plik qa_gate.jsonl → artefakt), manual_add.py (QA_GATE=1), qa_after_add.py (QA_GATE_FILE). Poprawki istniejących pozycji z błędem wracają do `pending` (QA_FIX=1).
   Działa w dwóch miejscach: ostatni krok `manual-add.yml` (każde ręczne dodanie: wyszukiwanie, WhatsApp, zrzuty)
   oraz `qa-after-bots.yml`, który startuje sam po każdym przebiegu bota dodającego lub poprawiającego wpisy
   (events, Instagram, hotele, newslettery, hints, uzupełnianie linków / godzin / opisów, nocna kontrola) i sprawdza
   wszystko zmienione od startu tego przebiegu. Sprawdza: duplikat (ten sam dzień, miasto, podobny tytuł),
   minione lub błędne daty, link do agregatora, martwy link (404, nieistniejąca domena), miasto, ofertę bez ceny
   i godziny. Zatwierdzona pozycja z błędem po bocie wraca do `pending` (znika z apki do przeglądu);
   przy ręcznym dodaniu run jest czerwony i poprawiam od razu.
8. **Pokrycie, przewodniki, siostrzane lokale** (decyzja 26.11.2026) – zadanie cotygodniowe (środa).
   `diag_coverage`: oferty na miasto × dzień × typ; luki (`GAP|`) uruchamiają celowane szukanie.
   Lokalne przewodniki (wow-rak, rakcalendar, wow-ajman) to tylko podpowiedź – każdą pozycję potwierdzam
   u lokalu / organizatora i nigdy nie daję ich jako linku. Raz w miesiącu `diag_brands`: marki lokali,
   które mamy w jednym emiracie, sprawdzam w innych (tak przeoczyliśmy CLAW BBQ RAK). Konta Instagram
   znalezionych lokali trafiają do bota.
