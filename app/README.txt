OutToday - jak uruchomić na telefonie

Wymagania: Node.js (wersja LTS z nodejs.org) na komputerze, Expo Go na telefonie,
komputer i telefon w tej samej sieci Wi-Fi.

1. Rozpakuj ten folder, np. do Dokumenty\outtoday.
2. Otwórz folder w Eksploratorze, kliknij w pasek adresu, wpisz: cmd  i naciśnij Enter.
3. W czarnym oknie wpisz po kolei (Enter po każdej linii):

   npm install
   npx expo start

4. Pojawi się kod QR. Zeskanuj go aparatem iPhone'a i wybierz "Otwórz w Expo Go".

Jeśli telefon nie może się połączyć, zatrzymaj (Ctrl+C) i uruchom:

   npx expo start --tunnel

Klucz do bazy jest w pliku src\config.ts. To klucz publiczny, tylko do odczytu.
