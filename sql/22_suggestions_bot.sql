-- Boty (klucz secret = service_role) mogą czytać i porządkować zgłoszenia.
grant select, update, delete on public.suggestions to service_role;
