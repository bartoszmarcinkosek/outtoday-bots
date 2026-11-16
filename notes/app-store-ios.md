# OutToday – wersja na iPhone'a i opis do App Store (gotowe, NIE wysłane)

Stan: 16.11.2026. Nic nie zostało wysłane do Apple. Wysyłka dopiero po aktywacji konta Julki i Twojej zgodzie.

## 1. Wersja na iPhone'a – co jest gotowe

- Identyfikator aplikacji (bundle ID): `ae.outtoday.app` – ten sam co na Androidzie.
- Wersja 1.0.0, build 1, tylko telefon, tylko pion.
- Teksty zgód iPhone'a (po angielsku, tak je zobaczy użytkownik):
  - Lokalizacja: „OutToday uses your location only to show how far events and places are from you. It is never stored or shared.”
  - Kalendarz: „OutToday adds events you choose to your calendar.”
- Szyfrowanie: zaznaczone, że aplikacja nie używa własnego szyfrowania. Dzięki temu Apple nie pyta o dokumenty eksportowe.
- Ikona 1024×1024 bez przezroczystości, czyli taka, jakiej wymaga Apple.
- Aktualizacje „w locie” (OTA) działają tak samo jak na Androidzie.

**Czego nie da się zrobić bez konta Apple:** samego pliku do App Store. Apple podpisuje go certyfikatem z konta Julki. Gdy konto będzie aktywne:
1. Julka w App Store Connect tworzy klucz API: Users and Access → Integrations → App Store Connect API → klucz z rolą „App Manager”. Pobiera plik `.p8` i zapisuje Key ID oraz Issuer ID.
2. Bartosz dodaje te trzy rzeczy do GitHub Secrets. Hasła i Apple ID zostają u Julki.
3. Budowanie i wysyłka do TestFlight idą przez GitHub Actions, tak jak Android.

## 2. Opis do App Store (po angielsku – do wklejenia)

**Nazwa (max 30):** OutToday

**Podtytuł (max 30):** UAE events, places & deals

**Tekst promocyjny (max 170, można zmieniać bez nowej wersji):**
What's on today across the UAE: concerts, festivals, brunches, happy hours, beaches and family days out, with prices and times from official pages.

**Opis:**

OutToday shows what's on across the UAE today, this weekend and in the weeks ahead, all in one free app.

EVENTS
Concerts, comedy, theatre, festivals, exhibitions, sports, markets, runs and family days out in Dubai, Abu Dhabi, Al Ain, Sharjah, Ras Al Khaimah and the other emirates. Each event shows the date, start time, venue and ticket price, with a link to the official or ticket page.

PLACES
Beaches, parks, museums, attractions, souks, kids' activities and day trips, with opening hours and entry prices where the venue publishes them.

DEALS
Weekly brunches, happy hours, ladies' nights, quiz nights, themed dinners and pool day passes, with the days, times and prices for each one.

MADE FOR EVERYDAY USE
• Filter by city, area, date, category, price and free entry
• See how far each place is from you
• Browse on the map
• Save favourites and add events to your calendar
• Share with friends and open directions in Google Maps or Waze
• No account, no sign-up

HONEST INFORMATION
We collect details from official venue, organiser and ticketing pages and check them every day. If something looks wrong, tap "Report a problem" and we will fix it.

OutToday is independent and is not affiliated with the venues or organisers listed. Always check the official page before you go.

**Słowa kluczowe (max 100, po przecinkach):**
dubai,abu dhabi,events,things to do,brunch,happy hour,ladies night,concerts,weekend,expat,sharjah

**Kategoria:** główna Lifestyle, druga Entertainment.

**Adresy:**
- Polityka prywatności: https://bartoszmarcinkosek.github.io/outtoday-web/privacy.html
- Pomoc (Support URL): https://bartoszmarcinkosek.github.io/outtoday-web/support.html
- Kontakt: outtodayapp.uae@gmail.com

**Copyright:** 2026 + imię i nazwisko Julki, takie jak w koncie Apple.

## 3. Ankiety Apple – jak odpowiedzieć

**Prywatność („App Privacy”): Data Not Collected.**
Aplikacja nie ma kont, reklam ani analityki. Lokalizacja zostaje w telefonie i służy tylko do liczenia odległości. Ulubione są zapisane tylko w telefonie. Do serwera idzie wyłącznie pobranie listy wydarzeń, bez danych użytkownika.

**Kategoria wiekowa:** w ofertach są happy hours i ladies' nights, więc przy pytaniu o alkohol trzeba zaznaczyć częste odniesienia do alkoholu. Wyjdzie najwyższa kategoria (18+). To zgadza się z naszą stroną prywatności, gdzie jest 18+. Pozostałe pytania: brak.

**Uwagi dla recenzenta (App Review notes):**
OutToday is a free, read-only guide to events, places and deals in the UAE. There is no login and no purchases. Content comes from official venue, organiser and ticketing pages and links back to them. Location is optional and used on-device only to show distance.

## 4. Do zrobienia przed wysyłką

- [ ] Konto Apple Developer Julki aktywne
- [ ] Aplikacja założona w App Store Connect (nazwa OutToday, bundle `ae.outtoday.app`)
- [ ] Klucz API (.p8 + Key ID + Issuer ID) dodany do GitHub Secrets
- [ ] Zrzuty ekranu z iPhone'a: Apple wymaga zestawu dla dużego ekranu (6,9 albo 6,5 cala). Zrobię je z aplikacji, gdy będzie build w TestFlight. Około 5 ekranów: lista eventów, szczegóły, mapa, oferty, filtry.
- [ ] Test w TestFlight na Twoim i Julki iPhonie
- [ ] Twoja zgoda → wysyłka do przeglądu Apple
