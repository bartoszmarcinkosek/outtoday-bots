# Kody kontroli spójności (bot/sanity.py) – co z nimi robić

Codzienny przegląd czyta ten plik. Każdą zgłoszoną pozycję trzeba rozstrzygnąć: poprawić albo oznaczyć jako sprawdzoną.
Oznaczanie: pary DUP_* → `audit/not_dups.txt` (`idA idB  # powód`); pozostałe kody z listy „tekst kontra pola",
CAME_BACK i VENUE_VARIANT → `audit/ok_flags.txt` (`KOD id  # powód`).

| Kod | Znaczenie | Działanie |
|---|---|---|
| CAME_BACK | Zatwierdzona pozycja dodana później niż bardzo podobna odrzucona – bot dodał znów to, co już ukryliśmy | Odrzuć, jeśli to ta sama rzecz, którą odrzucono z powodu treści (poza ZEA, zwykła cena, promocja, zła data). Zostaw i dopisz do ok_flags, gdy odrzucona była gorszą kopią tej (duplikat) albo gdy nowa ma poprawione dane |
| VENUE_VARIANT | To samo miejsce zapisane różnie albo z literówką | Ustaw `venue` na pisownię wskazaną w szczególe (ta częstsza / poprawna). Gdy to naprawdę dwa różne miejsca – ok_flags |
| DAY_MISMATCH, DAY_MISSING | Dni w tekście oferty inne niż w `days_of_week` (0 = niedziela … 6 = sobota) albo brak dni | Popraw pole albo tekst; gdy oba poprawne – ok_flags |
| TIME_MISMATCH, PRICE_MISMATCH, DATE_MISMATCH, FREE_TEXT_BUT_PRICE, CITY_IN_NAME | Tekst mówi co innego niż pola | Jak wyżej; w razie wątpliwości otwórz oficjalny link |
