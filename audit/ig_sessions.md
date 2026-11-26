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
| 25.11 | sesja ręczna 2: sport, muzea i galerie, sale i festiwale, atrakcje | Dubaj, Abu Zabi, Szardża, RAK, Al Ain (141 nazw) | +12 (pierwsza tura) i +37 (druga tura) = +49; sprawdzone w całości. Razem kont po sesji: 492 |
| 25.11 | konta z materiałów właściciela (WhatsApp): ADREA, NYUAD Arts Center, Socials RAK, Masala by Socials | Abu Zabi, RAK | w tym +4 (wliczone wyżej) |
| 25.11 | sesja 3: nazwy z oficjalnych stron (`diag_ighandles` czyta `audit/ig_sites.txt`: miasto / miejsce / strona) – atrakcje, centra handlowe, dzieci, teatry | 143 strony: 44 nowe nazwy, 42 istniały (przy zgadywaniu ok. 40%) | +38 |
| 25.11 | sesja 4: hotele małych emiratów, Al Ain, RAK, społeczności – 74 strony (`diag_ighandles`) + wyszukiwarka | strony hoteli i sieci w większości blokują pobieranie (robots), większość kont już była | wynik poniżej |

## Jeszcze nieprzeszukane (pomysły na kolejne sesje)
- Kalba i Dibba Al Hisn (dodane jako miejsca 25.11): konta EPAA Sharjah (centra w Kalbie), Mysk Kingfisher Retreat, gmina Kalby / Dibby – nazwy z oficjalnych stron (epaashj.ae, myskhotels) albo wyszukiwarki
- WAŻNE: w sesjach 1–2 połowa zgadywanych nazw nie istniała (m.in. duże atrakcje: Yas Waterworld, SeaWorld, Warner Bros. World, Zayed National Museum, teamLab Phenomena, IMG Worlds, Wild Wadi, KidZania, Dubai Parks, Ain Dubai, Sky Views, Museum of Illusions, Jubail Mangrove Park, House of Wisdom, Sharjah Safari, Aljada, Al Hamra Mall). Nie zgadywać – prawdziwą nazwę konta brać z oficjalnej strony miejsca albo z wyszukiwarki i dopiero wtedy sprawdzać przez API.
- hotele i resorty z własnym programem (brunche, noce tematyczne) – wg emiratów; strony sieci hotelowych blokują pobieranie, więc nazwy kont brać z wyszukiwarki
- miejsca, których strony nie dały nazwy konta w sesji 3 (blokada lub brak linku): Zayed National Museum, teamLab Phenomena, Jubail Mangrove Park, KidZania, Mall of the Emirates, City Centre Mirdif / Al Zahia / Ajman, Sky Views, Dubai Aquarium, Fun City, Magic Planet, Sharjah Safari, Al Montazah, 06 Mall, RAK Mall, Hili Fun City, Al Ain Mall, Al Ain Adventure, Umbrella Beach, UAQ Marine Club – nazwę znaleźć w wyszukiwarce
- centra handlowe i dzielnice (wydarzenia rodzinne, jarmarki)
- dzieci i rodzina: sale zabaw, edutainment, warsztaty
- teatry, kluby komediowe, kina plenerowe, organizatorzy koncertów
- społeczności: kluby biegowe, joga, targi i bazary, centra kultury (np. instytuty językowe)
- pustynia i przygoda: operatorzy, parki wodne, pola golfowe
- Ajman, Umm Al Quwain, Fudżajra, Al Ain – lokalne miejsca (najmniej kont)

`ig-discover` i `ig-mentions` warto powtarzać dopiero, gdy dojdzie dużo nowych źródeł / kont-węzłów (same z siebie dają wtedy nowe nazwy).
| 26.11 | sesja 5: `ig-mentions` (próba) – oznaczenia z 128 kont-węzłów, potem ręczny przegląd (bez osób, banków, marek spoza UAE) | 28 kandydatów, 8 wybranych (w tym 4 odrzucone przez filtr „brak UAE”, ale to znane miejsca UAE) | +8 (Dubaj 5, Abu Zabi 2, Fudżajra 1): Terra Expo City, The Club AD, Mawaheb, ATM, One Day Choir, Touch, Her Table, Fujairah Photography Award; razem 546 |
