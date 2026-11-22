import type { EventRow } from './api';

// 'today' | 'tomorrow' | 'weekend' | 'all' albo konkretna data w formacie RRRR-MM-DD.
export type DayFilter = string;

function iso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function addDays(d: Date, n: number): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  x.setDate(x.getDate() + n);
  return x;
}

// Zwraca zakres dat [od, do] dla wybranego filtra. Weekend to piątek, sobota i niedziela.
export function rangeFor(filter: DayFilter, now: Date = new Date()): [string, string] {
  const today = addDays(now, 0);
  if (/^\d{4}-\d{2}-\d{2}$/.test(filter)) return [filter, filter];
  if (filter === 'today') return [iso(today), iso(today)];
  if (filter === 'tomorrow') return [iso(addDays(today, 1)), iso(addDays(today, 1))];
  if (filter === 'weekend') {
    const dow = today.getDay(); // 0 = niedziela
    if (dow === 0) return [iso(today), iso(today)];
    const start = dow >= 5 ? today : addDays(today, 5 - dow);
    const end = addDays(today, 7 - dow);
    return [iso(start), iso(end)];
  }
  return [iso(today), '9999-12-31'];
}

export function inRange(e: EventRow, range: [string, string]): boolean {
  const start = e.start_date;
  const end = e.end_date ?? e.start_date;
  return start <= range[1] && end >= range[0];
}

export function isLongRunning(e: EventRow): boolean {
  if (!e.end_date) return false;
  const ms = new Date(e.end_date).getTime() - new Date(e.start_date).getTime();
  return ms > 10 * 24 * 3600 * 1000;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function parse(d: string): Date {
  const [y, m, day] = d.split('-').map(Number);
  return new Date(y, m - 1, day);
}

export function fmtDate(d: string, withYear = false): string {
  const x = parse(d);
  const y = withYear || x.getFullYear() !== new Date().getFullYear() ? ` ${x.getFullYear()}` : '';
  return `${DAYS[x.getDay()]} ${x.getDate()} ${MONTHS[x.getMonth()]}${y}`;
}

/** Zakres dat: trwające już wydarzenie -> "Until Sun 25 Apr 2027"; rok przy datach spoza bieżącego roku. */
function fmtRange(start: string, end: string): string {
  const today = new Date();
  const iso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  if (start < iso) return `Until ${fmtDate(end)}`;
  const span = start.slice(0, 4) !== end.slice(0, 4);
  return `${fmtDate(start, span)} to ${fmtDate(end, span)}`;
}

export function fmtTime(t: string | null): string | null {
  if (!t) return null;
  const hm = t.slice(0, 5);
  // W bazie północ na końcu dnia jest zapisana jako 23:59.
  return hm === '23:59' ? 'midnight' : hm;
}

function timePart(e: EventRow): string {
  const s = fmtTime(e.start_time);
  const en = fmtTime(e.end_time);
  if (s && en) return ` · ${s} to ${en}`;
  if (s) return ` · from ${s}`;
  return '';
}

// Wydarzenie długie, które już trwa: na liście pokazujemy tylko datę końca.
export function isOngoing(e: EventRow, now: Date = new Date()): boolean {
  return isLongRunning(e) && e.start_date < iso(now);
}

export function fmtCardWhen(e: EventRow, now: Date = new Date()): string {
  if (isOngoing(e, now) && e.end_date) {
    return `Until ${fmtDate(e.end_date)}${timePart(e)}`;
  }
  return fmtWhen(e);
}

export function fmtWhen(e: EventRow): string {
  const date =
    e.end_date && e.end_date !== e.start_date
      ? fmtRange(e.start_date, e.end_date)
      : fmtDate(e.start_date);
  const s = fmtTime(e.start_time);
  const en = fmtTime(e.end_time);
  if (s && en) return `${date} · ${s} to ${en}`;
  if (s) return `${date} · from ${s}`;
  return date;
}

export function fmtDays(days: number[] | null): string {
  if (!days || days.length === 0) return 'Days to confirm';
  if (days.length === 7) return 'Every day';
  return days.map((d) => DAYS[d]).join(', ');
}

export function todayDow(now: Date = new Date()): number {
  return now.getDay();
}

// Kolejne dni do wyboru w pasku dat (od pojutrza, bo Today i Tomorrow mają własne przyciski).
export function upcomingDays(count: number, now: Date = new Date()): { key: string; label: string }[] {
  const out: { key: string; label: string }[] = [];
  for (let i = 2; i < 2 + count; i++) {
    const key = iso(addDays(now, i));
    out.push({ key, label: fmtDate(key) });
  }
  return out;
}

export const DOW_CHIPS: { dow: number; label: string }[] = [
  { dow: 1, label: 'Mon' },
  { dow: 2, label: 'Tue' },
  { dow: 3, label: 'Wed' },
  { dow: 4, label: 'Thu' },
  { dow: 5, label: 'Fri' },
  { dow: 6, label: 'Sat' },
  { dow: 0, label: 'Sun' },
];
