# Szukanie kont Instagram – co już było przeszukane

Zasada: nie powtarzać tego samego wyszukiwania. Przed nową sesją przeczytaj ten plik i wybierz kategorię / sposób, którego tu nie ma.
Konta już na liście (`sources/instagram.json`) i nazwy odrzucone (`audit/ig_rejected.txt`, ważne 180 dni) są pomijane automatycznie,
bez zapytania do Instagrama – przez `diag_igcheck`, `ig-discover` i `ig-mentions`.
Wynik sprawdzenia zapisuje `python bot/ig_apply.py <log> [--skip konto,konto]` (dodaje dobre, odrzucone dopisuje do listy, czyści kandydatów).

| Data | Sposób / kategoria | Zakres | Wynik |
|---|---|---|---|
| 17.11–24.11 | materiały właściciela (WhatsApp), ręczne szukanie dla małych emiratów | Al Ain, Ajman, UAQ, Fudżajra, RAK | +38 |
| 25.11 | Khor Fakkan | plaża, amfiteatr, Najd Al Meqsar, Railway Café | +4 |
| 25.11 | `ig-discover` – linki do Instagrama na oficjalnych stronach wszystkich naszych źródeł | wszystkie emiraty | +22 |
| 25.11 | `ig-mentions` – nazwy kont w opisach postów kont-węzłów (urzędy turystyki, areny, dzielnice + konta bez miejsca) | wszystkie emiraty | 139 kandydatów, +26 |
| 25.11 | sesja ręczna 1: restauracje, bary, puby, beach cluby | Dubaj, Abu Zabi, RAK, Fudżajra (87 nazw) | +31 |
| 25.11 | sesja ręczna 2: sport, muzea i galerie, sale i festiwale, atrakcje | Dubaj, Abu Zabi, Szardża, RAK, Al Ain (141 nazw) | +12 (pierwsza tura) i +44 (druga tura, 16:10) = +56; sprawdzone w całości |
| 25.11 | konta z materiałów właściciela (WhatsApp): ADREA, NYUAD Arts Center, Socials RAK, Masala by Socials | Abu Zabi, RAK | w tym +4 (wliczone wyżej) |

## Jeszcze nieprzeszukane (pomysły na kolejne sesje)
- hotele i resorty z własnym programem (brunche, noce tematyczne) – wg emiratów
- centra handlowe i dzielnice (wydarzenia rodzinne, jarmarki)
- dzieci i rodzina: sale zabaw, edutainment, warsztaty
- teatry, kluby komediowe, kina plenerowe, organizatorzy koncertów
- społeczności: kluby biegowe, joga, targi i bazary, centra kultury (np. instytuty językowe)
- pustynia i przygoda: operatorzy, parki wodne, pola golfowe
- Ajman, Umm Al Quwain, Fudżajra, Al Ain – lokalne miejsca (najmniej kont)

`ig-discover` i `ig-mentions` warto powtarzać dopiero, gdy dojdzie dużo nowych źródeł / kont-węzłów (same z siebie dają wtedy nowe nazwy).
