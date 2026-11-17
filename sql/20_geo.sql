-- OutToday: współrzędne miejsc (dokładne pinezki na mapie i dokładne odległości).
-- Wklej w Supabase: SQL Editor -> New query -> Run. Można uruchomić wiele razy.
alter table events add column if not exists lat double precision;
alter table events add column if not exists lng double precision;
alter table places add column if not exists lat double precision;
alter table places add column if not exists lng double precision;
alter table deals  add column if not exists lat double precision;
alter table deals  add column if not exists lng double precision;
