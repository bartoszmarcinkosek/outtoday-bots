# outtoday-bots

Boty, które zbierają eventy do aplikacji OutToday z **oficjalnych stron** organizatorów.

## Jak to działa
1. `sources/*.json`: lista stron (tylko oficjalne strony miejsc i organizatorów).
2. Bot otwiera stronę w przeglądarce, sprawdza robots.txt i pomija strony, które zabraniają botom wejścia.
3. AI (Claude Haiku) wypisuje eventy **tylko z tekstu strony**, z dosłownymi cytatami.
4. Program sprawdza każdy cytat. Jeśli daty, ceny lub miejsca nie ma na stronie, pole zostaje puste i trafia do braków.
5. Nowe wpisy idą do bazy jako `pending`, więc apka ich nie pokazuje, dopóki ich nie zatwierdzicie.
6. Zmiany w zatwierdzonych wpisach (np. cena) idą do `bot_changes` do porannego e-maila. Nic nie jest nadpisywane.

## Uruchomienie
Zakładka **Actions**, potem **Events bot**, potem **Run workflow**.
- `dry_run` zaznaczone: próba bez zapisu, tylko raport (podsumowanie na stronie uruchomienia i plik `raport` do pobrania).
- `dry_run` odznaczone: zapis do bazy jako `pending`.

## Jednorazowo w Supabase
Uruchom `sql/12_bots.sql` w Supabase SQL Editor przed pierwszym zapisem do bazy.

## Sekrety (Settings, Secrets and variables, Actions)
`ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`. Nigdy nie wpisuj ich do plików.
