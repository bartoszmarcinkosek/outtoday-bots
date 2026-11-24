import { Ionicons } from '@expo/vector-icons';
import * as Calendar from 'expo-calendar/legacy';
import React, { useState } from 'react';
import { Image, Linking, Platform, Pressable, Share, StyleSheet, Text, View } from 'react-native';
import { sendSuggestion } from './api';
import { fmtDate } from './dates';
import { IconName, Item, todayIso } from './logic';
import { PHOTO_FULL } from './photos.gen';
import { count } from './stats';
import { colors } from './theme';
import { Pill, Sheet, badgesFor } from './ui';
import { CITIES, ZONES, ZONE_CENTER, distanceKm } from './zones';

// ---------- Wybór miasta i dzielnic ----------

export function LocationSheet(props: {
  visible: boolean; onClose: () => void; city: string; zones: string[];
  available: Record<string, string[]>; // miasto -> rejony, w których coś jest
  counts: Record<string, number>; // miasto -> liczba pozycji
  onChange: (city: string, zones: string[]) => void;
  me?: [number, number] | null; // lokalizacja telefonu: najbliższe rejony na górze
}) {
  // Rejony: najbliższy pierwszy (gdy znamy lokalizację), inaczej alfabetycznie.
  const km = (key: string) => (props.me && ZONE_CENTER[key] ? distanceKm(props.me, ZONE_CENTER[key]) : null);
  const zoneList = ZONES.filter((z) => (props.available[props.city] ?? []).includes(z.key))
    .map((z) => ({ ...z, km: km(z.key) }))
    .sort((a, b) => (a.km != null && b.km != null ? a.km - b.km : a.label.localeCompare(b.label)));
  const toggle = (key: string) => {
    const next = props.zones.includes(key) ? props.zones.filter((z) => z !== key) : [...props.zones, key];
    props.onChange(props.city, next);
  };
  return (
    <Sheet visible={props.visible} onClose={props.onClose} title="Where?"
      footer={<BigButton label="Done" onPress={props.onClose} />}>
      <Text style={styles.section}>City</Text>
      {CITIES.map((c) => (
        <Row key={c} label={props.counts[c] ? c : `${c} · coming soon`}
          icon={props.city === c ? 'radio-button-on' : 'radio-button-off'}
          active={props.city === c} onPress={() => props.onChange(c, [])} />
      ))}
      {zoneList.length > 1 && (
        <>
          <Text style={styles.section}>Areas in {props.city}</Text>
          <Row label={`All ${props.city}`} icon={props.zones.length === 0 ? 'checkbox' : 'square-outline'}
            active={props.zones.length === 0} onPress={() => props.onChange(props.city, [])} />
          {zoneList.map((z) => (
            <Row key={z.key} label={z.km != null ? `${z.label} · ${z.km < 10 ? z.km.toFixed(1) : Math.round(z.km)} km` : z.label} icon={props.zones.includes(z.key) ? 'checkbox' : 'square-outline'}
              active={props.zones.includes(z.key)} onPress={() => toggle(z.key)} />
          ))}
        </>
      )}
    </Sheet>
  );
}

function Row(props: { label: string; icon: IconName; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={props.onPress} style={styles.row}>
      <Ionicons name={props.icon} size={22} color={props.active ? colors.primary : colors.muted} />
      <Text style={[styles.rowText, props.active && { color: colors.text, fontWeight: '600' }]}>{props.label}</Text>
    </Pressable>
  );
}

export function BigButton(props: { label: string; onPress: () => void; icon?: IconName; quiet?: boolean }) {
  return (
    <Pressable onPress={props.onPress} style={[styles.big, props.quiet && styles.bigQuiet]}>
      {props.icon && <Ionicons name={props.icon} size={18} color={props.quiet ? colors.text : colors.bg} style={{ marginRight: 8 }} />}
      <Text style={[styles.bigText, props.quiet && { color: colors.text }]}>{props.label}</Text>
    </Pressable>
  );
}

// ---------- Kalendarz ----------

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export function CalendarSheet(props: { visible: boolean; onClose: () => void; selected: string | null; onPick: (iso: string) => void }) {
  const now = new Date();
  const [offset, setOffset] = useState(0);
  const first = new Date(now.getFullYear(), now.getMonth() + offset, 1);
  const days = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
  const lead = (first.getDay() + 6) % 7; // tydzień zaczyna się w poniedziałek
  const today = todayIso(now);
  const cells: (string | null)[] = [];
  for (let i = 0; i < lead; i++) cells.push(null);
  for (let d = 1; d <= days; d++) cells.push(todayIso(new Date(first.getFullYear(), first.getMonth(), d)));
  while (cells.length % 7 !== 0) cells.push(null);
  return (
    <Sheet visible={props.visible} onClose={props.onClose} title="Pick a date">
      <View style={styles.calHead}>
        <Pressable onPress={() => setOffset(Math.max(0, offset - 1))} hitSlop={12} disabled={offset === 0}>
          <Ionicons name="chevron-back" size={24} color={offset === 0 ? colors.border : colors.text} />
        </Pressable>
        <Text style={styles.calTitle}>{MONTH_NAMES[first.getMonth()]} {first.getFullYear()}</Text>
        <Pressable onPress={() => setOffset(Math.min(11, offset + 1))} hitSlop={12}>
          <Ionicons name="chevron-forward" size={24} color={colors.text} />
        </Pressable>
      </View>
      <View style={styles.calGrid}>
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
          <Text key={d} style={[styles.calCell, styles.calDow]}>{d}</Text>
        ))}
        {cells.map((iso, i) => {
          const past = !!iso && iso < today;
          const sel = !!iso && iso === props.selected;
          return (
            <Pressable key={i} style={styles.calCell} disabled={!iso || past}
              onPress={() => { if (iso) { props.onPick(iso); props.onClose(); } }}>
              {!!iso && (
                <View style={[styles.calDay, sel && { backgroundColor: colors.primary }, iso === today && !sel && styles.calToday]}>
                  <Text style={{ color: sel ? colors.bg : past ? colors.border : colors.text, fontWeight: sel ? '700' : '400' }}>
                    {Number(iso.slice(8))}
                  </Text>
                </View>
              )}
            </Pressable>
          );
        })}
      </View>
    </Sheet>
  );
}

// ---------- Szczegóły ----------

function open(url: string) {
  Linking.openURL(url).catch(() => undefined);
}

async function addToCalendar(item: Item) {
  const e = item.event;
  if (!e) return;
  const today = todayIso();
  const day = e.start_date >= today ? e.start_date : today;
  const [y, m, d] = day.split('-').map(Number);
  const at = (t: string | null, fallbackHour: number) => {
    const [h, min] = (t ?? `${fallbackHour}:00`).split(':').map(Number);
    return new Date(y, m - 1, d, h, min);
  };
  const start = at(e.start_time, 9);
  const end = e.end_time ? at(e.end_time, 10) : new Date(start.getTime() + 2 * 3600 * 1000);
  try {
    await Calendar.createEventInCalendarAsync({
      title: e.title, startDate: start, endDate: end > start ? end : new Date(start.getTime() + 3600 * 1000),
      allDay: !e.start_time, location: item.where ?? undefined, notes: item.priceText ?? undefined,
      // przypomnienia: dzień wcześniej i 2 godziny przed (iPhone; na Androidzie kalendarz dodaje swoje domyślne)
      alarms: [{ relativeOffset: -24 * 60 }, { relativeOffset: -120 }],
    });
  } catch {
    // Użytkownik zamknął okno kalendarza albo telefon go nie obsługuje.
  }
}

// proporcje dużego zdjęcia (kwadrat albo 2:3 dla wysokich budynków, np. Burj Khalifa)
function ratioOf(src: number): number {
  const a = Image.resolveAssetSource(src);
  return a && a.width && a.height ? a.width / a.height : 1;
}

const REPORT_REASONS = ['Wrong date or time', 'Wrong price', 'Cancelled or sold out', 'Wrong place', 'Photo does not fit', 'Something else'];

// Na przycisku widać, dokąd prowadzi link (prośba testera: Instagram bywa zablokowany w pracy).
const SOCIAL: [RegExp, string, string][] = [
  [/instagram\.com/i, 'Instagram', 'logo-instagram'], [/facebook\.com|fb\.me/i, 'Facebook', 'logo-facebook'],
  [/tiktok\.com/i, 'TikTok', 'logo-tiktok'], [/(twitter|x)\.com/i, 'X (Twitter)', 'logo-twitter'],
  [/youtube\.com|youtu\.be/i, 'YouTube', 'logo-youtube'], [/wa\.me|whatsapp\.com/i, 'WhatsApp', 'logo-whatsapp'],
  [/linkedin\.com/i, 'LinkedIn', 'logo-linkedin'], [/meetup\.com/i, 'Meetup', 'people-outline'],
];
function host(url: string): string {
  const h = (url.match(/^https?:\/\/([^/?#]+)/i)?.[1] ?? url).replace(/^www\./i, '').toLowerCase();
  return h.length > 26 ? h.slice(0, 25) + '…' : h;
}
export function linkLabel(url: string, ticketing: boolean): string {
  const soc = SOCIAL.find(([re]) => re.test(url));
  if (soc) return `Open on ${soc[1]}`;
  return `${ticketing ? 'Tickets' : 'Website'} · ${host(url)}`;
}
function linkIcon(url: string): any {
  return SOCIAL.find(([re]) => re.test(url))?.[2] ?? 'open-outline';
}

export function DetailSheet(props: { item: Item | null; photo?: number | null; fav: boolean; onFav: () => void; onClose: () => void; nearby?: Item[]; onPick?: (i: Item) => void }) {
  const [reporting, setReporting] = useState<'closed' | 'open' | 'sending' | 'sent'>('closed');
  const [reportFor, setReportFor] = useState<string | null>(null);
  const item = props.item;
  if (!item) return null;
  if (reportFor !== item.key && reporting !== 'closed') { setReporting('closed'); }
  if (reportFor !== item.key) setReportFor(item.key);
  const c = item.look;
  const q = encodeURIComponent(item.mapQuery);
  const share = () => {
    // link do strony wpisu na naszej stronie (działa też u osób bez apki)
    const link = `https://outtodayapp.github.io/e/${item.key.replace(':', '-')}.html`; // strona ze zdjęciem (podgląd w WhatsApp)
    const lines = [item.title, item.whenFull, item.where, item.priceText, '', `More on OutToday: ${link}`];
    count('share', `${item.kind}:${item.catKey ?? ''}`);
    // iPhone: link osobno (url), wtedy WhatsApp robi podgląd ze zdjęciem; Android: link w tekście
    const text = lines.filter(Boolean).join('\n');
    if (Platform.OS === 'ios') {
      Share.share({ message: [item.title, item.whenFull, item.where, item.priceText].filter(Boolean).join('\n'), url: link }).catch(() => undefined);
    } else {
      Share.share({ message: text }).catch(() => undefined);
    }
  };
  // Zgłoszenie problemu trafia do tabeli suggestions → poranny mail do zespołu (bez maila po stronie użytkownika).
  const report = (reason: string) => {
    setReporting('sending');
    sendSuggestion({
      title: `Report: ${item.title}`.slice(0, 150), note: `Problem: ${reason}. Item: ${item.key}`,
      link: item.officialUrl ?? undefined, city: item.city, venue: item.where ?? undefined,
    }).then(() => setReporting('sent')).catch(() => setReporting('open'));
    count('report', reason, item.city);
  };
  const isTicketing = /platinumlist|feverup|eventbrite|sevenrooms/i.test(item.officialUrl ?? '');
  const digits = (item.phone ?? '').replace(/[^\d+]/g, '');
  const facts: [string, string | null][] = [
    [item.kind === 'place' ? 'Hours' : 'When', item.whenFull],
    ['Where', item.where],
    ['Price', item.free ? item.priceText ?? 'Free' : item.priceText],
    ['Booking', item.booking ? 'Registration required' : null],
    ['Good to know', [item.kid && 'Kid-friendly', item.pet && 'Pet-friendly', item.ladies && 'Ladies only',
      item.indoor === true && 'Indoor', item.kind === 'place' && item.indoor === false && 'Outdoor'].filter(Boolean).join(' · ') || null],
  ];
  return (
    <Sheet visible onClose={props.onClose} title={item.title}>
      {!!props.photo && (
        <View style={[styles.bigPhoto, { aspectRatio: ratioOf(PHOTO_FULL.get(props.photo) ?? props.photo) }, ratioOf(PHOTO_FULL.get(props.photo) ?? props.photo) < 1 && { width: '70%' }]}>
          <Image source={PHOTO_FULL.get(props.photo) ?? props.photo} resizeMode="cover"
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }} />
        </View>
      )}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 }}>
        <Pill text={c.label} color={c.accent} />
        {item.free && <Pill text="FREE" color={colors.free} solid />}
        {badgesFor(item).map((b) => <Pill key={b} text={b} color={c.accent} solid />)}
      </View>
      {!!item.description && <Text style={styles.desc}>{item.description}</Text>}
      {facts.filter(([, v]) => !!v).map(([k, v]) => (
        <View key={k} style={styles.fact}>
          <Text style={styles.factKey}>{k}</Text>
          <Text style={styles.factVal}>{v}</Text>
        </View>
      ))}
      {item.event && item.event.end_date && item.endsSoon && (
        <Text style={styles.note}>Last day: {fmtDate(item.event.end_date)}</Text>
      )}
      <View style={styles.actions}>
        <Action icon={props.fav ? 'heart' : 'heart-outline'} label={props.fav ? 'Saved' : 'Save'} onPress={props.onFav} />
        <Action icon="share-outline" label="Share" onPress={share} />
        <Action icon="map-outline" label="Google Maps" onPress={() => { count('map', `gmaps:${item.kind}`, item.city); open(`https://www.google.com/maps/dir/?api=1&destination=${item.geo ? `${item.geo[0]},${item.geo[1]}` : q}`); }} />
        <Action icon="navigate-outline" label="Waze" onPress={() => { count('map', `waze:${item.kind}`, item.city); open(item.geo ? `https://waze.com/ul?ll=${item.geo[0]},${item.geo[1]}&navigate=yes` : `https://waze.com/ul?q=${q}&navigate=yes`); }} />
        {item.kind === 'event' && <Action icon="alarm-outline" label="Remind me" onPress={() => addToCalendar(item)} />}
        {!!digits && <Action icon="call-outline" label="Call" onPress={() => { count('map', `call:${item.kind}`, item.city); open(`tel:${digits}`); }} />}
        {!!digits && <Action icon="logo-whatsapp" label="WhatsApp" onPress={() => open(`https://wa.me/${digits.replace('+', '')}`)} />}
      </View>
      {!!item.officialUrl && (
        <BigButton label={linkLabel(item.officialUrl!, isTicketing)} icon={linkIcon(item.officialUrl!)} onPress={() => { open(item.officialUrl!); count('item', `${isTicketing ? 'tickets' : 'official'}:${item.kind}:${item.catKey ?? ''}`, item.city); }} />
      )}
      {!!props.nearby?.length && (
        <View style={{ marginTop: 8 }}>
          <Text style={styles.section}>Before or after</Text>
          {props.nearby.map((n) => (
            <Pressable key={n.key} onPress={() => props.onPick?.(n)} style={styles.nearRow}>
              <Ionicons name={n.icon} size={20} color={n.look.accent} />
              <View style={{ flex: 1, marginLeft: 10 }}>
                <Text style={styles.nearTitle} numberOfLines={1}>{n.title}</Text>
                <Text style={styles.nearSub} numberOfLines={1}>{[n.when, n.where].filter(Boolean).join(' · ')}</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={colors.muted} />
            </Pressable>
          ))}
        </View>
      )}
      {item.verified && (
        <Text style={styles.note}>Verified with the organiser{item.checked ? ` · ${item.checked}` : ''}</Text>
      )}
      {reporting === 'closed' && (
        <Pressable onPress={() => setReporting('open')} style={{ paddingVertical: 10 }}>
          <Text style={styles.report}>Something not right? Tell us</Text>
        </Pressable>
      )}
      {(reporting === 'open' || reporting === 'sending') && (
        <View style={{ marginTop: 10 }}>
          <Text style={styles.section}>What is wrong?</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {REPORT_REASONS.map((r) => (
              <Pressable key={r} disabled={reporting === 'sending'} onPress={() => report(r)} style={styles.action}>
                <Text style={styles.actionText}>{r}</Text>
              </Pressable>
            ))}
          </View>
        </View>
      )}
      {reporting === 'sent' && <Text style={styles.note}>Thanks! We will check it against the official page.</Text>}
    </Sheet>
  );
}

function Action(props: { icon: IconName; label: string; onPress: () => void }) {
  return (
    <Pressable onPress={props.onPress} style={styles.action}>
      <Ionicons name={props.icon} size={20} color={colors.primary} />
      <Text style={styles.actionText}>{props.label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  // całe zdjęcie kategorii (kwadrat) na górze szczegółów
  bigPhoto: { width: '100%', maxWidth: 420, alignSelf: 'center', borderRadius: 14, overflow: 'hidden', marginBottom: 12, backgroundColor: 'rgba(0,0,0,0.22)' },
  section: { color: colors.muted, fontSize: 13, fontWeight: '700', marginTop: 12, marginBottom: 4, textTransform: 'uppercase' },
  soon: { color: colors.muted, fontSize: 13, marginTop: 4 },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: 11 },
  rowText: { color: colors.muted, fontSize: 16, marginLeft: 12 },
  big: {
    flexDirection: 'row', backgroundColor: colors.primary, borderRadius: 14, paddingVertical: 14,
    alignItems: 'center', justifyContent: 'center', marginTop: 12,
  },
  bigQuiet: { backgroundColor: colors.chip, borderWidth: 1, borderColor: colors.border },
  bigText: { color: colors.bg, fontSize: 16, fontWeight: '700' },
  calHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  calTitle: { color: colors.text, fontSize: 17, fontWeight: '700' },
  calGrid: { flexDirection: 'row', flexWrap: 'wrap' },
  calCell: { width: `${100 / 7}%`, height: 44, alignItems: 'center', justifyContent: 'center', textAlign: 'center' },
  calDow: { color: colors.muted, fontSize: 12, height: 26, textAlignVertical: 'center' },
  calDay: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  calToday: { borderWidth: 1, borderColor: colors.primary },
  desc: { color: colors.text, fontSize: 15, lineHeight: 21, marginBottom: 10 },
  fact: { flexDirection: 'row', paddingVertical: 7, borderTopWidth: 1, borderTopColor: colors.border },
  factKey: { color: colors.muted, width: 104, fontSize: 14 },
  factVal: { color: colors.text, flex: 1, fontSize: 14 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 12 },
  action: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.chip, borderRadius: 12, borderWidth: 1,
    borderColor: colors.border, paddingHorizontal: 12, paddingVertical: 10, marginRight: 8, marginBottom: 8,
  },
  actionText: { color: colors.text, fontSize: 14, marginLeft: 7 },
  note: { color: colors.muted, fontSize: 12, marginTop: 12, lineHeight: 17 },
  nearRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.muted },
  nearTitle: { color: colors.text, fontSize: 15, fontWeight: '600' },
  nearSub: { color: colors.muted, fontSize: 13, marginTop: 2 },
  report: { color: colors.muted, fontSize: 13, textDecorationLine: 'underline' },
});
