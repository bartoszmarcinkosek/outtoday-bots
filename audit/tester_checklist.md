# Lista kontrolna nocnego testera kart (rośnie z każdym nowym rodzajem błędu)
Format: data | rodzaj błędu | przykład | jak naprawione (reguła / plik)

2026-11-26 | Free pokazuje płatne: Meetup („Free” = darmowy zapis) | Heels & Chair, padel, badminton | bot/run.py: Meetup nigdy is_free; price_min_aed czyszczone
2026-11-26 | Free pokazuje płatne: spektakl w galerii z wolnym wstępem | The Game's Afoot (The Junction, Alserkal) | bot/run.py free_entry_applies tylko wystawy
2026-11-26 | Ladies only pusty | Heels & Chair (Ladies Only) | app/src/logic.ts LADIES_RE z tytułu i opisu
2026-11-26 | Mężczyźni/pary na zdjęciu pozycji tylko dla pań | Heels & Chair | photos.ts: klucz dance_ladies (ikonka do czasu zdjęcia)
2026-11-26 | Zdjęcie pokoju przy afternoon tea | Afternoon Tea at La Farine (typ staycation) | typ → lunch; photos.ts klucz afternoon_tea
2026-11-26 | Zdjęcie pokoju przy staycation w beach resorcie | Fairmont Fujairah Beach Resort | photos.ts: beach resort → day_pass
2026-11-26 | Wyścigi konne przy targach łowieckich | Al Ain Hunting & Equestrian Exhibition | photos.ts: hunting exhibition → expo
2026-11-26 | Plaża przy wieczorze DJ w beach clubie; fort przy miejscowości Dibba Al Hisn; dolina górska przy pustyni | Lost Frequencies at Bohemia; Dibba Al Hisn Beach; Al Wadi Desert | photos.ts reguły
2026-11-26 | Wydarzenie powtarza stałe miejsce | La Perle (miejsce + „wydarzenie do 31.12”) | qa_after_add: długie wydarzenie = nazwa miejsca → FAIL
2026-11-26 | Wyprzedaż w centrum handlowym jako wydarzenie | 12-Day Super Sale, Reem Mall | qa_after_add: sale/discount → FAIL
2026-11-26 | Niezrozumiały tytuł | „BWP 1” (gala MMA) | tytuł poprawiony ręcznie
2026-11-26 | Rodzinne wydarzenie poza filtrem Kids | Aladdin at Al Qasba | diag_filters (niedziela)
2026-11-26 | Brunch z Mikołajem bez świątecznego zdjęcia | Santa brunch Market Kitchen | photos.ts santa/christmas → xmas
