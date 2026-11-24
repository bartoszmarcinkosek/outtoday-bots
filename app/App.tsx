import * as Updates from 'expo-updates';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { noteItemOpened } from './src/review';
import * as Location from 'expo-location';
import { StatusBar } from 'expo-status-bar';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator, FlatList, Linking, Modal, Platform, Pressable, RefreshControl, ScrollView, Share, StyleSheet, Text, TextInput, View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { AppData, fetchAll, loadCached } from './src/api';
import { photoFor } from './src/photos';
import { count } from './src/stats';
import { DOW_CHIPS, fmtDate, inRange, rangeFor } from './src/dates';
import {
  Item, SORT_LABEL, Shortcut, SortKey, buildItems, dealEndedToday, dealOnDay, dealOnNow, searchItems, shortcutsFor, sortItems, todayIso,
  placeOpen, nearbyDeals,
} from './src/logic';
import { ZoneMap } from './src/map';
import { SuggestSheet } from './src/suggest';
import { AboutSheet } from './src/about';
import { BigButton, CalendarSheet, DetailSheet, LocationSheet } from './src/sheets';
import { cat, colors, dealStyle } from './src/theme';
import { Chip, Empty, ItemCard, Sheet } from './src/ui';
import { hasTop10 } from './src/top10';
import { CITY_CENTER, ZONES, ZONE_CENTER, distanceKm } from './src/zones';

type Tab = 'today' | 'events' | 'places' | 'deals';
type ListTab = Exclude<Tab, 'today'>;
type InOut = 'all' | 'in' | 'out';

const TABS: { key: Tab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }[] = [
  { key: 'today', label: 'Today', icon: 'sunny-outline' },
  { key: 'events', label: 'Events', icon: 'calendar-outline' },
  { key: 'places', label: 'Places', icon: 'location-outline' },
  { key: 'deals', label: 'Deals', icon: 'pricetag-outline' },
];
const DAY_CHIPS = [
  { key: 'today', label: 'Today' },
  { key: 'tomorrow', label: 'Tomorrow' },
  { key: 'weekend', label: 'Weekend' },
  { key: 'all', label: 'All upcoming' },
];
const PRICE_CAPS = [100, 200, 300];
const PREFS_KEY = 'outtoday.prefs.v1';
const FAVS_KEY = 'outtoday.favs.v1';
const VISIT_KEY = 'outtoday.lastVisit.v1';
// Mapa na Androidzie wymaga klucza Google Maps w buildzie (app.json) – do tego czasu tylko iPhone (Apple Maps).
const MAP_OK = Platform.OS === 'ios';
// Listopad–marzec: sezon na wyjścia, więc "Outdoor" idzie pierwsze. Latem pierwsze jest "Indoor (AC)".
const OUTDOOR_SEASON = [10, 11, 0, 1, 2].includes(new Date().getMonth());
const INTERESTS_KEY = 'outtoday.interests.v1';
// Kategorie eventów do wyboru przy pierwszym uruchomieniu (ekran Dziś pokazuje je wyżej).
const INTEREST_KEYS = ['music', 'culture', 'sport', 'food', 'family', 'nightlife', 'festivals', 'classes', 'nature', 'community', 'market'];
const USAGE_KEY = 'outtoday.filterUse.v1';
const KIND_OF: Record<ListTab, Item['kind']> = { events: 'event', places: 'place', deals: 'deal' };

// Pierwsze uruchomienie po instalacji ze sklepu działa na wersji wbudowanej w paczkę (starej, bez nowych zdjęć).
// Wtedy od razu pobieramy najnowszą aktualizację i przeładowujemy, zamiast czekać do następnego otwarcia.
function useFreshOnFirstLaunch() {
  useEffect(() => {
    if (__DEV__ || !Updates.isEnabled || !Updates.isEmbeddedLaunch) return;
    (async () => {
      try {
        const r = await Updates.checkForUpdateAsync();
        if (r.isAvailable) {
          await Updates.fetchUpdateAsync();
          await Updates.reloadAsync();
        }
      } catch { /* brak sieci – zostaje wersja wbudowana */ }
    })();
  }, []);
}

export default function App() {
  useFreshOnFirstLaunch();
  return (
    <SafeAreaProvider>
      <Main />
    </SafeAreaProvider>
  );
}

function Main() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [me, setMe] = useState<[number, number] | null>(null);

  const [tab, setTab] = useState<Tab>('today');
  const [city, setCity] = useState('Abu Dhabi');
  const [zones, setZones] = useState<string[]>([]);
  const [favs, setFavs] = useState<string[]>([]);

  // Filtry
  const [day, setDay] = useState('today');
  const [dealDay, setDealDay] = useState<number | null>(null);
  const [topOnly, setTopOnly] = useState(false);
  const [openOnly, setOpenOnly] = useState(false);
  const [cats, setCats] = useState<Record<ListTab, string[]>>({ events: [], places: [], deals: [] }); // kilka kategorii naraz
  const [sorts, setSorts] = useState<Record<ListTab, SortKey>>({ events: 'default', places: 'default', deals: 'default' });
  const [free, setFree] = useState(false);
  const [kid, setKid] = useState(false);
  const [pet, setPet] = useState(false);
  const [ladies, setLadies] = useState(false);
  const [inOut, setInOut] = useState<InOut>('all');
  const [cap, setCap] = useState<number | null>(null);
  const [evening, setEvening] = useState(false);
  const [lastChance, setLastChance] = useState(false); // tylko eventy, które wkrótce się kończą
  const [interests, setInterests] = useState<string[] | null>(null); // null = jeszcze nie wybrano
  const [showInterests, setShowInterests] = useState(false);

  // Okna
  const [selected, setSelected] = useState<Item | null>(null);
  const [selPhoto, setSelPhoto] = useState<number | null>(null);
  const [showWhere, setShowWhere] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showCal, setShowCal] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [prevVisit, setPrevVisit] = useState<number | null>(null);
  const [showFavs, setShowFavs] = useState(false);
  const [showSuggest, setShowSuggest] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
  const [query, setQuery] = useState('');
  const [view, setView] = useState<'list' | 'map'>('list');
  // Ile razy użyto każdego filtra. Najczęstsze trafiają na górę panelu filtrów.
  const [usage, setUsage] = useState<Record<string, number>>({});
  const [usageSnap, setUsageSnap] = useState<Record<string, number>>({});

  const load = useCallback(async () => {
    try {
      setData(await fetchAll());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => { count('open'); }, []);

  useEffect(() => {
    (async () => {
      let hasCity = false; // czy użytkownik już kiedyś wybrał miasto
      const cached = await loadCached();
      if (cached) setData(cached);
      try {
        const prefs = JSON.parse((await AsyncStorage.getItem(PREFS_KEY)) ?? 'null');
        if (prefs?.city) { setCity(prefs.city); hasCity = true; }
        if (Array.isArray(prefs?.zones)) setZones(prefs.zones);
        const u = JSON.parse((await AsyncStorage.getItem(USAGE_KEY)) ?? '{}');
        if (u && typeof u === 'object') setUsage(u);
        const f = JSON.parse((await AsyncStorage.getItem(FAVS_KEY)) ?? '[]');
        if (Array.isArray(f)) setFavs(f);
        // "Co nowego": licznik wpisów dodanych od poprzedniej wizyty.
        const ints = JSON.parse((await AsyncStorage.getItem(INTERESTS_KEY)) ?? 'null');
        if (Array.isArray(ints)) setInterests(ints); else setShowInterests(true);
        const lv = Number(await AsyncStorage.getItem(VISIT_KEY));
        if (lv > 0) setPrevVisit(lv);
        AsyncStorage.setItem(VISIT_KEY, String(Date.now())).catch(() => undefined);
      } catch {
        // Brak zapisanych ustawień: zostają domyślne.
      }
      load();
      // Lokalizacja służy tylko do sortowania "najbliżej mnie". Bez zgody apka działa dalej.
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          const pos = (await Location.getLastKnownPositionAsync()) ??
            (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Low }));
          if (pos) {
            const here: [number, number] = [pos.coords.latitude, pos.coords.longitude];
            setMe(here);
            // Pierwsze uruchomienie: zaczynamy od najbliższego miasta.
            if (!hasCity) {
              const nearest = Object.entries(CITY_CENTER)
                .map(([c, v]) => [c, distanceKm(here, [v[0], v[1]])] as const)
                .sort((a, b) => a[1] - b[1])[0];
              if (nearest && nearest[1] < 60) setCity(nearest[0]);
            }
          }
        }
      } catch {
        // Brak lokalizacji: sortujemy po dacie i nazwie.
      }
    })();
  }, [load]);

  const changeWhere = (c: string, z: string[]) => {
    setCity(c);
    setZones(z);
    AsyncStorage.setItem(PREFS_KEY, JSON.stringify({ city: c, zones: z })).catch(() => undefined);
  };
  const saveInterests = (keys: string[]) => {
    setInterests(keys);
    setShowInterests(false);
    AsyncStorage.setItem(INTERESTS_KEY, JSON.stringify(keys)).catch(() => undefined);
    count('interests', keys.join(',') || 'none');
  };
  // Plan na weekend: zapisane (serduszko) nadchodzące eventy jednym tekstem do wysłania znajomym.
  const sharePlan = () => {
    const up = sortItems(all.filter((i) => favs.includes(i.key) && i.kind === 'event'), 'default');
    if (!up.length) return;
    const lines = up.slice(0, 12).map((i) => `• ${i.title}\n  ${[i.when, i.where].filter(Boolean).join(' · ')}\n  https://outtodayapp.github.io/e/${i.key.replace(':', '-')}.html`);
    Share.share({ message: `Our plan 🗓\n\n${lines.join('\n\n')}\n\nFound on OutToday: https://outtodayapp.github.io` }).catch(() => undefined);
    count('plan', String(up.length), city);
  };
  // anonimowo: co ludzie wpisują w wyszukiwarkę i ile wyników dostali ("0|..." = szukali czegoś, czego nie mamy)
  const logSearch = (q: string) => {
    const t = q.trim().toLowerCase();
    if (t.length < 2) return;
    count('search', `${searchItems(all, t).length > 0 ? 'ok' : '0'}|${t}`, city);
  };
  const toggleFav = (key: string) => {
    setFavs((prev) => {
      const adding = !prev.includes(key);
      const it = adding ? all.find((i) => i.key === key) : undefined;
      if (adding) count('item', `fav:${it ? `${it.kind}:${it.catKey ?? ''}` : key.split(':')[0]}`, city);
      const next = prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key];
      AsyncStorage.setItem(FAVS_KEY, JSON.stringify(next)).catch(() => undefined);
      return next;
    });
  };

  const bump = (key: string) => {
    setUsage((prev) => {
      const next = { ...prev, [key]: (prev[key] ?? 0) + 1 };
      AsyncStorage.setItem(USAGE_KEY, JSON.stringify(next)).catch(() => undefined);
      return next;
    });
  };
  const openFilters = () => { setUsageSnap(usage); setShowFilters(true); };

  const all = useMemo(() => (data ? buildItems(data, me) : []), [data, me]);
  const nearDeals = useMemo(() => (selected ? nearbyDeals(selected, all) : []), [selected, all]);

  // Rejony dostępne w każdym mieście (tylko te, w których coś jest).
  const available = useMemo(() => {
    const out: Record<string, string[]> = {};
    for (const i of all) {
      if (!i.zone) continue;
      (out[i.city] ??= []);
      if (!out[i.city].includes(i.zone)) out[i.city].push(i.zone);
    }
    return out;
  }, [all]);

  const cityCounts = useMemo(() => {
    const out: Record<string, number> = {};
    for (const i of all) out[i.city] = (out[i.city] ?? 0) + 1;
    return out;
  }, [all]);

  // Wszystko w wybranym mieście i dzielnicach, przed pozostałymi filtrami.
  const local = useMemo(
    () => all.filter((i) => i.city === city && (zones.length === 0 || (!!i.zone && zones.includes(i.zone)))),
    [all, city, zones],
  );

  const newItems = useMemo(
    () => (prevVisit ? local.filter((i) => i.created && Date.parse(i.created) > prevVisit) : []),
    [local, prevVisit],
  );

  const initialLinkDone = useRef(false);
  // Link outtoday://item?id=event:<uuid> (ze strony udostępnionego wpisu) otwiera ten wpis w apce.
  useEffect(() => {
    const openUrl = (url?: string | null) => {
      const id = url ? decodeURIComponent((url.match(/[?&]id=([^&]+)/) ?? [])[1] ?? '') : '';
      const hit = id ? all.find((i) => i.key === id) : undefined;
      if (hit) { setSelPhoto(photoFor(hit)); setSelected(hit); }
    };
    if (all.length && !initialLinkDone.current) {
      initialLinkDone.current = true;
      Linking.getInitialURL().then(openUrl).catch(() => undefined);
    }
    const sub = Linking.addEventListener('url', (e) => openUrl(e.url));
    return () => sub.remove();
  }, [all]);

  const listFor = useCallback(
    (t: ListTab, wholeCity = false): Item[] => {
      const range = rangeFor(day);
      // Top 10 zawsze dla całego miasta, niezależnie od wybranego obszaru.
      const base = wholeCity || (t === 'places' && topOnly && hasTop10(city)) ? all.filter((i) => i.city === city) : local;
      const filtered = base
        .filter((i) => i.kind === KIND_OF[t])
        .filter((i) => cats[t].length === 0 || (i.catKey != null && cats[t].includes(i.catKey)))
        .filter((i) => !free || i.free)
        .filter((i) => !kid || i.kid)
        .filter((i) => !pet || i.pet)
        .filter((i) => !ladies || i.ladies)
        .filter((i) => t !== 'events' || inRange(i.event!, range))
        .filter((i) => t !== 'events' || !evening || (i.event!.start_time ?? '') >= '17:00')
        .filter((i) => t !== 'events' || !lastChance || i.endsSoon)
        .filter((i) => t !== 'places' || inOut === 'all' || i.indoor === (inOut === 'in'))
        .filter((i) => t !== 'places' || !topOnly || !hasTop10(city) || i.top != null)
        .filter((i) => t !== 'places' || !openOnly || placeOpen(i.place)?.open === true)
        .filter((i) => t !== 'deals' || dealDay === null || dealOnDay(i.deal!, dealDay))
        .filter((i) => t === 'places' || cap === null || (i.price !== null && i.price <= cap));
      if (t === 'places' && topOnly && hasTop10(city) && sorts[t] === 'default') return [...filtered].sort((a, b) => (a.top ?? 99) - (b.top ?? 99));
      return sortItems(filtered, sorts[t]);
    },
    [local, all, cats, free, kid, pet, ladies, day, inOut, dealDay, cap, sorts, topOnly, openOnly, city, evening, lastChance],
  );

  const list = useMemo(() => (tab === 'today' ? [] : listFor(tab)), [tab, listFor]);
  // Pusto w wybranej dzielnicy (np. Reem Island)? Pokaż to, co jest najbliżej (do 8 km), zamiast pustego ekranu.
  const nearby = useMemo(() => {
    if (tab === 'today' || list.length > 0 || zones.length === 0) return [];
    const centers = zones.map((z) => ZONE_CENTER[z]).filter(Boolean) as [number, number][];
    if (!centers.length) return [];
    const dist = (i: Item) => {
      const p = i.geo ?? (i.zone ? ZONE_CENTER[i.zone] : null);
      return p ? Math.min(...centers.map((c) => distanceKm(c, p as [number, number]))) : Infinity;
    };
    return listFor(tab, true).map((i) => ({ i, d: dist(i) })).filter((x) => x.d <= 8).sort((a, b) => a.d - b.d).map((x) => x.i).slice(0, 30);
  }, [tab, list, zones, listFor]);

  const catKeys = useMemo(() => {
    if (tab === 'today') return [];
    const present = new Set(local.filter((i) => i.kind === KIND_OF[tab]).map((i) => i.catKey));
    const lbl = (k: string) => (tab === 'deals' ? dealStyle(k) : cat(k)).label;
    return [...present].filter(Boolean).sort((a, b) => lbl(a).localeCompare(lbl(b)));
  }, [tab, local]);

  const activeCount =
    (tab === 'events' ? 0 : Number(free) + Number(kid)) + Number(pet) + Number(ladies) + (tab === 'events' && evening ? 1 : 0) + (tab === 'events' && lastChance ? 1 : 0) +
    (tab !== 'today' ? cats[tab].length : 0) + (tab === 'places' && inOut !== 'all' ? 1 : 0) + (tab === 'places' && topOnly ? 1 : 0) + (tab === 'places' && openOnly ? 1 : 0) +
    ((tab === 'deals' || tab === 'events') && cap !== null ? 1 : 0);

  const clearFilters = () => {
    setFree(false); setKid(false); setPet(false); setLadies(false); setEvening(false); setLastChance(false); setInOut('all'); setCap(null); setTopOnly(false); setOpenOnly(false);
    setCats({ events: [], places: [], deals: [] });
  };

  // Przejście z ekranu Today albo z wyszukiwarki do gotowej listy.
  const jump = (s: { tab: ListTab; key?: string | null; day?: string; dealDay?: number | null; free?: boolean; ending?: boolean }) => {
    clearFilters();
    setCats({ events: [], places: [], deals: [], [s.tab]: s.key ? [s.key] : [] } as Record<ListTab, string[]>);
    if (s.day) setDay(s.day);
    if (s.dealDay !== undefined) setDealDay(s.dealDay);
    if (s.free) setFree(true);
    if (s.ending) setLastChance(true);
    setShowSearch(false);
    setQuery('');
    setTab(s.tab);
  };

  const whereLabel = zones.length === 0
    ? city
    : `${city} · ${zones.map((z) => ZONES.find((x) => x.key === z)?.label ?? z).join(', ')}`;
  const isDate = /^\d{4}-\d{2}-\d{2}$/.test(day);
  const labelFor = (t: ListTab, key: string) => (t === 'deals' ? dealStyle(key) : cat(key));
  // idx/arr przychodzą z .map() i FlatList – dzięki nim sąsiednie karty dostają różne zdjęcia
  const card = (item: Item, idx?: number, arr?: readonly Item[]) => {
    const prev = arr && idx ? arr[idx - 1] : undefined;
    const photo = photoFor(item, prev ? photoFor(prev) : null);
    return (
      <ItemCard key={item.key} item={item} photo={photo} fav={favs.includes(item.key)}
        onFav={() => toggleFav(item.key)} onPress={() => { setSelPhoto(photo); setSelected(item); count('item', `${item.kind}:${item.catKey ?? ''}`, city); noteItemOpened(); }} />
    );
  };
  const refreshControl = (
    <RefreshControl refreshing={refreshing} tintColor={colors.primary}
      onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} />
  );

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'left', 'right']}>
      <StatusBar style="light" />

      <View style={styles.header}>
        <View style={{ flex: 1 }}>
          <Pressable onPress={() => setShowAbout(true)} hitSlop={6} accessibilityLabel="About OutToday" style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={styles.brand}>OutToday</Text>
            <Ionicons name="information-circle-outline" size={18} color={colors.muted} style={{ marginLeft: 6, marginTop: 4 }} />
          </Pressable>
          <Pressable onPress={() => setShowWhere(true)} style={styles.where} hitSlop={8}>
            <Ionicons name="location" size={15} color={colors.primary} />
            <Text style={styles.whereText} numberOfLines={1}>{whereLabel}</Text>
            <Ionicons name="chevron-down" size={15} color={colors.primary} />
          </Pressable>
        </View>
        <Pressable onPress={() => setShowSuggest(true)} hitSlop={10} style={styles.headBtn} accessibilityLabel="Suggest an event">
          <Ionicons name="add-circle-outline" size={28} color={colors.text} />
        </Pressable>
        <Pressable onPress={() => setShowSearch(true)} hitSlop={10} style={styles.headBtn}>
          <Ionicons name="search" size={27} color={colors.text} />
        </Pressable>
        <Pressable onPress={() => setShowFavs(true)} hitSlop={10} style={styles.headBtn}>
          <Ionicons name={favs.length ? 'heart' : 'heart-outline'} size={27} color={favs.length ? '#FF8FA3' : colors.text} />
        </Pressable>
      </View>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>Could not refresh. Showing saved data. {error}</Text>
        </View>
      )}

      {newItems.length > 0 && (
        <Pressable onPress={() => { setShowNew(true); count('new'); }} style={styles.newBanner} accessibilityLabel="New since your last visit">
          <Ionicons name="sparkles" size={16} color={colors.primary} />
          <Text style={styles.newBannerText}>
            {newItems.length} new {newItems.length === 1 ? 'listing' : 'listings'} since your last visit
          </Text>
          <Ionicons name="chevron-forward" size={16} color={colors.primary} />
        </Pressable>
      )}

      {!data ? (
        <ActivityIndicator color={colors.primary} style={{ marginTop: 60 }} />
      ) : tab === 'today' ? (
        <TodayScreen local={local} card={card} jump={jump} refreshControl={refreshControl} interests={interests ?? []} onInterests={() => setShowInterests(true)} />
      ) : (
        <>
          {tab === 'events' && (
            <View style={styles.chipRow}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRowIn}>
              {DAY_CHIPS.map((d) => (
                <Chip key={d.key} label={d.label} active={day === d.key} onPress={() => setDay(d.key)} />
              ))}
              <Chip label={isDate ? fmtDate(day) : 'Pick a date'} icon="calendar-outline" active={isDate} onPress={() => setShowCal(true)} />
              <View style={styles.chipSep} />
              <Chip label="Evening" icon="moon-outline" active={evening} onPress={() => { setEvening(!evening); count('filter', 'quick:evening', city); }} />
              <Chip label="Last chance" icon="hourglass-outline" active={lastChance} onPress={() => { setLastChance(!lastChance); count('filter', 'quick:last', city); }} />
            </ScrollView>
            </View>
          )}
          {tab === 'places' && (
            <View style={styles.chipRow}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRowIn}>
              <Chip label="All places" active={!topOnly && !openOnly} onPress={() => { setTopOnly(false); setOpenOnly(false); }} />
              <Chip label="Open now" icon="time-outline" active={openOnly} onPress={() => setOpenOnly(!openOnly)} />
              {(OUTDOOR_SEASON ? (['out', 'in'] as const) : (['in', 'out'] as const)).map((v) => (
                <Chip key={v} label={v === 'out' ? 'Outdoor' : 'Indoor (AC)'} icon={v === 'out' ? 'sunny-outline' : 'snow-outline'}
                  active={inOut === v} onPress={() => { setInOut(inOut === v ? 'all' : v); count('filter', `quick:${v}`, city); }} />
              ))}
              {hasTop10(city) && (
                <Chip label={`Top 10 in ${city}`} icon="trophy-outline" active={topOnly} onPress={() => setTopOnly(!topOnly)} />
              )}
            </ScrollView>
            </View>
          )}
          {tab === 'deals' && (
            <View style={styles.chipRow}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRowIn}>
              <Chip label="Any day" active={dealDay === null} onPress={() => setDealDay(null)} />
              <Chip label="Today" active={dealDay === new Date().getDay()} onPress={() => setDealDay(new Date().getDay())} />
              {DOW_CHIPS.filter((d) => d.dow !== new Date().getDay()).map((d) => (
                <Chip key={d.dow} label={d.label} active={dealDay === d.dow} onPress={() => setDealDay(d.dow)} />
              ))}
            </ScrollView>
            </View>
          )}

          <View style={styles.toolbar}>
            <Pressable onPress={openFilters} style={[styles.tool, activeCount > 0 && styles.toolOn]}>
              <Ionicons name="options-outline" size={19} color={activeCount > 0 ? colors.bg : colors.text} />
              <Text style={[styles.toolText, activeCount > 0 && { color: colors.bg, fontWeight: '700' }]}>
                Filters{activeCount > 0 ? ` (${activeCount})` : ''}
              </Text>
            </Pressable>
            {activeCount > 0 && (
              <Pressable onPress={clearFilters} style={styles.tool}>
                <Text style={styles.toolText}>Clear</Text>
              </Pressable>
            )}
            {tab === 'events' && (['free', 'kids'] as const).map((k) => {
              const on = k === 'free' ? free : kid;
              return (
                <Pressable key={k} style={[styles.tool, on && styles.toolOn]}
                  onPress={() => { if (k === 'free') setFree(!free); else setKid(!kid); count('filter', `quick:${k}`, city); }}>
                  <Ionicons name={k === 'free' ? 'pricetag-outline' : 'happy-outline'} size={17} color={on ? colors.bg : colors.text} />
                  <Text style={[styles.toolText, on && { color: colors.bg, fontWeight: '700' }]}>{k === 'free' ? 'Free' : 'Kids'}</Text>
                </Pressable>
              );
            })}
            {MAP_OK && <Pressable onPress={() => setView(view === 'list' ? 'map' : 'list')} style={styles.tool} accessibilityLabel={view === 'list' ? 'Map' : 'List'}>
              <Ionicons name={view === 'list' ? 'map-outline' : 'list-outline'} size={19} color={colors.text} />
              {tab !== 'events' && <Text style={styles.toolText}>{view === 'list' ? 'Map' : 'List'}</Text>}
            </Pressable>}
            <View style={{ flex: 1 }} />
            <Text style={styles.count}>{list.length}{tab === 'events' ? '' : list.length === 1 ? ' result' : ' results'}</Text>
          </View>
          {cats[tab].length > 0 && (
            <Text style={styles.activeCat}>Showing: {cats[tab].map((k) => labelFor(tab, k).label).join(', ')}</Text>
          )}

          {MAP_OK && view === 'map' ? (
            <ZoneMap items={list} city={city} card={card} />
          ) : (
            <FlatList
              data={list.length ? list : nearby}
              keyExtractor={(i) => i.key}
              renderItem={({ item, index }) => card(item, index, list.length ? list : nearby)}
              contentContainerStyle={styles.list}
              refreshControl={refreshControl}
              ListHeaderComponent={!list.length && nearby.length ? (
                <Text style={styles.todayDate}>Nothing in {whereLabel.split(' · ')[1] ?? 'this area'} for these filters. Closest to it:</Text>
              ) : undefined}
              ListEmptyComponent={<Empty text="Nothing matches these filters. Try another day, area or fewer filters." />}
            />
          )}
        </>
      )}

      <SafeAreaView edges={['bottom']} style={styles.tabBar}>
        {TABS.map((t) => (
          <Pressable key={t.key} style={styles.tabBtn} onPress={() => { setTab(t.key); setView('list'); count('tab', t.key, city); }}>
            <Ionicons name={t.icon} size={26} color={tab === t.key ? colors.primary : colors.muted} />
            <Text style={[styles.tabText, tab === t.key && { color: colors.primary, fontWeight: '700' }]}>{t.label}</Text>
          </Pressable>
        ))}
      </SafeAreaView>

      <LocationSheet visible={showWhere} onClose={() => setShowWhere(false)} city={city} zones={zones} available={available} counts={cityCounts} onChange={changeWhere} me={me} />
      <CalendarSheet visible={showCal} onClose={() => setShowCal(false)} selected={isDate ? day : null} onPick={setDay} />

      {tab !== 'today' && (
        <Sheet visible={showFilters} onClose={() => setShowFilters(false)} title="Filters"
          footer={<BigButton label={`Show ${list.length} ${list.length === 1 ? 'result' : 'results'}`} onPress={() => setShowFilters(false)} />}>
          <Text style={styles.section}>Sort by</Text>
          <View style={styles.wrap}>
            {(['default', 'near', 'price'] as SortKey[]).map((s) => (
              <Chip key={s} label={SORT_LABEL[s]} active={sorts[tab] === s} onPress={() => setSorts({ ...sorts, [tab]: s })} />
            ))}
          </View>
          {!me && <Text style={styles.hint}>Allow location access in Settings to sort by distance.</Text>}

          <Text style={styles.section}>Show only</Text>
          <View style={styles.wrap}>
            {([
              { key: 'free', label: 'Free', on: free, set: setFree, color: colors.free },
              { key: 'kid', label: 'Kid-friendly', on: kid, set: setKid },
              { key: 'ladies', label: 'Ladies only', on: ladies, set: setLadies },
              { key: 'pet', label: 'Pet-friendly', on: pet, set: setPet },
            ] as { key: string; label: string; on: boolean; set: (v: boolean) => void; color?: string }[])
              .sort((a, b) => (usageSnap[`toggle:${b.key}`] ?? 0) - (usageSnap[`toggle:${a.key}`] ?? 0) || a.label.localeCompare(b.label))
              .map((t) => (
                <Chip key={t.key} label={t.label} active={t.on} color={t.color}
                  onPress={() => { if (!t.on) bump(`toggle:${t.key}`); t.set(!t.on); }} />
              ))}
          </View>

          {tab === 'places' && (
            <>
              <Text style={styles.section}>Indoor or outdoor</Text>
              <View style={styles.wrap}>
                <Chip label="Both" active={inOut === 'all'} onPress={() => setInOut('all')} />
                <Chip label="Indoor" active={inOut === 'in'} onPress={() => setInOut('in')} />
                <Chip label="Outdoor" active={inOut === 'out'} onPress={() => setInOut('out')} />
              </View>
            </>
          )}

          {(tab === 'deals' || tab === 'events') && (
            <>
              <Text style={styles.section}>Price</Text>
              <View style={styles.wrap}>
                <Chip label="Any price" active={cap === null} onPress={() => setCap(null)} />
                {PRICE_CAPS.map((p) => (
                  <Chip key={p} label={`Up to AED ${p}`} active={cap === p} onPress={() => setCap(p)} />
                ))}
              </View>
            </>
          )}

          {(() => {
            const use = (k: string) => usageSnap[`${tab}:${k}`] ?? 0;
            const top = [...catKeys].filter((k) => use(k) >= 2).sort((a, b) => use(b) - use(a)).slice(0, 4);
            const rest = catKeys.filter((k) => !top.includes(k));
            const chip = (k: string) => {
              const c = labelFor(tab, k);
              return (
                <Chip key={k} label={c.label} color={c.accent} active={cats[tab].includes(k)}
                  onPress={() => {
                    const on = cats[tab].includes(k);
                    if (!on) bump(`${tab}:${k}`);
                    setCats({ ...cats, [tab]: on ? cats[tab].filter((x) => x !== k) : [...cats[tab], k] });
                  }} />
              );
            };
            return (
              <>
                {top.length > 0 && (
                  <>
                    <Text style={styles.section}>Your favourites</Text>
                    <View style={styles.wrap}>{top.map(chip)}</View>
                  </>
                )}
                <Text style={styles.section}>{tab === 'deals' ? 'All types' : 'All categories'}</Text>
                <View style={styles.wrap}>
                  <Chip label="All" active={cats[tab].length === 0} onPress={() => setCats({ ...cats, [tab]: [] })} />
                  {rest.map(chip)}
                </View>
              </>
            );
          })()}
          {activeCount > 0 && <BigButton label="Clear all filters" quiet onPress={clearFilters} />}
        </Sheet>
      )}

      <SearchScreen visible={showSearch} onClose={() => { logSearch(query); setShowSearch(false); setQuery(''); }} query={query} setQuery={setQuery}
        items={all} city={city} card={card} jump={jump}
        detail={
          <DetailSheet item={showSearch ? selected : null} fav={!!selected && favs.includes(selected.key)}
            onFav={() => selected && toggleFav(selected.key)} photo={selPhoto} onClose={() => setSelected(null)}
            nearby={nearDeals} onPick={(n) => { setSelPhoto(photoFor(n)); setSelected(n); }} />
        } />

      <AboutSheet visible={showAbout} onClose={() => setShowAbout(false)} onSuggest={() => setShowSuggest(true)} />
      <SuggestSheet visible={showSuggest} onClose={() => setShowSuggest(false)} city={city} />
      <Modal visible={showFavs} animationType="slide" onRequestClose={() => setShowFavs(false)}>
        <SafeAreaProvider>
          <SafeAreaView style={styles.screen}>
            <View style={styles.header}>
              <Text style={[styles.brand, { flex: 1 }]}>Saved</Text>
              {all.some((i) => favs.includes(i.key) && i.kind === 'event') && (
                <Pressable onPress={sharePlan} hitSlop={10} style={[styles.tool, { marginRight: 14 }]} accessibilityLabel="Share your plan">
                  <Ionicons name="share-outline" size={18} color={colors.text} />
                  <Text style={styles.toolText}>Share plan</Text>
                </Pressable>
              )}
              <Pressable onPress={() => setShowFavs(false)} hitSlop={10}>
                <Ionicons name="close" size={26} color={colors.text} />
              </Pressable>
            </View>
            <FlatList
              data={sortItems(all.filter((i) => favs.includes(i.key)), 'default')}
              keyExtractor={(i) => i.key}
              renderItem={({ item }) => card(item)}
              contentContainerStyle={styles.list}
              ListEmptyComponent={<Empty text="Nothing saved yet. Tap the heart on any card to keep it here." />}
            />
            <DetailSheet item={showFavs ? selected : null} fav={!!selected && favs.includes(selected.key)}
              onFav={() => selected && toggleFav(selected.key)} photo={selPhoto} onClose={() => setSelected(null)}
            nearby={nearDeals} onPick={(n) => { setSelPhoto(photoFor(n)); setSelected(n); }} />
          </SafeAreaView>
        </SafeAreaProvider>
      </Modal>

      <InterestsSheet visible={showInterests && !!data} initial={interests ?? []} onSave={saveInterests} />

      <Modal visible={showNew} animationType="slide" onRequestClose={() => setShowNew(false)}>
        <SafeAreaProvider>
          <SafeAreaView style={styles.screen}>
            <View style={styles.header}>
              <Text style={[styles.brand, { flex: 1 }]}>New for you</Text>
              <Pressable onPress={() => setShowNew(false)} hitSlop={10}>
                <Ionicons name="close" size={26} color={colors.text} />
              </Pressable>
            </View>
            <FlatList
              data={sortItems(newItems, 'default')}
              keyExtractor={(i) => i.key}
              renderItem={({ item }) => card(item)}
              contentContainerStyle={styles.list}
              ListEmptyComponent={<Empty text="Nothing new since your last visit." />}
            />
            <DetailSheet item={showNew ? selected : null} fav={!!selected && favs.includes(selected.key)}
              onFav={() => selected && toggleFav(selected.key)} photo={selPhoto} onClose={() => setSelected(null)}
            nearby={nearDeals} onPick={(n) => { setSelPhoto(photoFor(n)); setSelected(n); }} />
          </SafeAreaView>
        </SafeAreaProvider>
      </Modal>

      <DetailSheet item={showFavs || showSearch || showNew ? null : selected} fav={!!selected && favs.includes(selected.key)}
        onFav={() => selected && toggleFav(selected.key)} photo={selPhoto} onClose={() => setSelected(null)}
            nearby={nearDeals} onPick={(n) => { setSelPhoto(photoFor(n)); setSelected(n); }} />
    </SafeAreaView>
  );
}

type Jump = (s: { tab: ListTab; key?: string | null; day?: string; dealDay?: number | null; free?: boolean; ending?: boolean }) => void;

// Duże, znane miejsca i wydarzenia idą na górę ekranu Today (stała lista, bez śledzenia użytkowników).
const BIG = /etihad arena|etihad park|coca[- ]cola arena|space ?42|louvre|guggenheim|dubai opera|expo city|global village|yas marina|yas island|yas bay|ferrari world|warner bros|qasr al watan|sheikh zayed festival|liwa|al dhafra festival|mother of the nation|motn|zayed sports city|hazza bin zayed|mohammed bin zayed stadium|dubai sevens|the sevens|museum of the future|cultural foundation|manarat al saadiyat|sharjah light|al majaz|al qasba|dp world|meydan|grand prix|formula 1|f1 |marathon|festival|national day|eid al etihad/i;

const toMin = (t?: string | null) => (t ? Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5)) : null);

// Kolejność „On today”: 1) to, co dziś jeszcze trwa lub się zacznie, 2) duże wydarzenia,
// 3) start w ciągu 3 godzin, 4) reszta w dotychczasowej kolejności. Na dół to, co już się dziś skończyło.
function rankToday(items: Item[], now: Date): Item[] {
  const nowMin = now.getHours() * 60 + now.getMinutes();
  const today = todayIso(now);
  const score = (i: Item) => {
    const e = i.event!;
    const start = e.start_date === today ? toMin(e.start_time) : null;
    let end = toMin(e.end_time) ?? (start !== null && !e.end_date ? start + 180 : null);
    if (end !== null && start !== null && end < start) end += 1440; // po północy
    if (end !== null && (!e.end_date || e.end_date === today) && end <= nowMin) return 9;
    let s = 3;
    if (BIG.test(`${i.title} ${e.venue ?? ''}`)) s = 0;
    else if (start !== null && start >= nowMin - 30 && start <= nowMin + 180) s = 1;
    else if (start !== null && start > nowMin) s = 2;
    return s;
  };
  return items.map((it, k) => ({ it, k, s: score(it) })).sort((a, b) => a.s - b.s || a.k - b.k).map((x) => x.it);
}

// Ekran startowy: co dzieje się dziś w wybranym mieście.
function TodayScreen(props: {
  local: Item[]; card: (i: Item) => React.ReactNode; jump: Jump; refreshControl: React.ReactElement<any>;
  interests: string[]; onInterests: () => void;
}) {
  const now = new Date();
  const today = todayIso(now);
  const range: [string, string] = [today, today];
  // Wybrane zainteresowania idą na górę (kolejność w obrębie grupy bez zmian).
  const liked = (i: Item) => (props.interests.includes(i.catKey) ? 0 : 1);
  const byInterest = (xs: Item[]) => (props.interests.length ? xs.map((it, k) => ({ it, k })).sort((a, b) => liked(a.it) - liked(b.it) || a.k - b.k).map((x) => x.it) : xs);
  const events = sortItems(props.local.filter((i) => i.event && inRange(i.event, range)), 'default');
  const single = events.filter((i) => !i.endsSoon && i.event!.start_date === today);
  const ranked = byInterest(rankToday([...single, ...events.filter((i) => !single.includes(i))], now));
  // Od 15:00: osobno "Dziś wieczorem" – jednodniowe eventy, które jeszcze się nie zaczęły.
  const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const tonight = now.getHours() >= 15
    ? ranked.filter((i) => i.event!.start_date === today && !!i.event!.start_time && i.event!.start_time.slice(0, 5) >= hm)
    : [];
  const onToday = ranked.filter((i) => !tonight.includes(i));
  // "For you": najbliższe 7 dni w wybranych kategoriach (żeby wybór było widać, nawet gdy dziś nic z nich nie ma).
  const week: [string, string] = [today, todayIso(new Date(now.getTime() + 6 * 86400000))];
  const forYou = props.interests.length
    ? sortItems(props.local.filter((i) => i.event && props.interests.includes(i.catKey) && inRange(i.event, week)), 'default')
    : [];
  const freeToday = onToday.filter((i) => i.free);
  const deals = props.local.filter((i) => i.deal && dealOnDay(i.deal, now.getDay()));
  const rank = (i: Item) => (dealOnNow(i.deal!, now) ? 0 : dealEndedToday(i.deal!, now) ? 2 : 1);
  const dealsSorted = sortItems(deals, 'default').sort((a, b) => rank(a) - rank(b));
  // "Last chance": wystawy, festiwale i promocje, które kończą się w ciągu tygodnia (najpierw te, które kończą się najszybciej).
  const endOf = (i: Item) => i.event?.end_date ?? i.deal?.valid_until ?? '9999';
  const ending = sortItems(props.local.filter((i) => (i.kind === 'event' || i.kind === 'deal') && i.endsSoon), 'default')
    .sort((a, b) => endOf(a).localeCompare(endOf(b)));
  // Od czwartku: najlepsze rzeczy na weekend (piątek–niedziela). Duże wydarzenia i krótkie eventy najpierw.
  const dow = now.getDay();
  const wk = rangeFor('weekend', now);
  const weekend = dow === 4 || dow === 5
    ? sortItems(props.local.filter((i) => i.event && inRange(i.event, wk) && !(dow === 5 && i.event.start_date === today && onToday.includes(i))), 'default')
        .map((it, k) => ({ it, k, s: (BIG.test(`${it.title} ${it.event!.venue ?? ''}`) ? 0 : 2) + (it.event!.end_date && it.event!.end_date !== it.event!.start_date ? 1 : 0) }))
        .sort((a, b) => a.s - b.s || a.k - b.k).map((x) => x.it)
    : [];

  const section = (title: string, items: Item[], max: number, onAll: () => void) =>
    items.length === 0 ? null : (
      <View key={title} style={{ marginBottom: 10 }}>
        <View style={styles.secHead}>
          <Text style={styles.secTitle}>{title}</Text>
          <Pressable onPress={onAll} hitSlop={10}>
            <Text style={styles.seeAll}>See all {items.length}</Text>
          </Pressable>
        </View>
        {items.slice(0, max).map(props.card)}
      </View>
    );

  const blocks = [
    section('Tonight', tonight, 5, () => props.jump({ tab: 'events', day: 'today' })),
    section('For you this week', forYou, 5, () => props.jump({ tab: 'events', day: 'all', key: props.interests.length === 1 ? props.interests[0] : null })),
    section(tonight.length ? 'Also on today' : 'On today', onToday, tonight.length ? 3 : 5, () => props.jump({ tab: 'events', day: 'today' })),
    section('This weekend', byInterest(weekend), 5, () => props.jump({ tab: 'events', day: 'weekend' })),
    section('Last chance', ending, 4, () => props.jump({ tab: 'events', day: 'all', ending: true })),
    section('Free today', freeToday, 4, () => props.jump({ tab: 'events', day: 'today', free: true })),
    section('Deals today', dealsSorted, 5, () => props.jump({ tab: 'deals', dealDay: now.getDay() })),
  ].filter(Boolean);

  return (
    <ScrollView contentContainerStyle={styles.list} refreshControl={props.refreshControl}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 10 }}>
        <Text style={[styles.todayDate, { flex: 1, marginBottom: 0 }]}>{fmtDate(today)}</Text>
        <Pressable onPress={props.onInterests} hitSlop={10}>
          <Text style={styles.seeAll}>{props.interests.length ? 'For you ✓' : 'Personalise'}</Text>
        </Pressable>
      </View>
      {blocks.length > 0 ? blocks : <Empty text="Nothing listed for today in this area. Try a wider area or check the Events tab." />}
    </ScrollView>
  );
}

function InterestsSheet(props: { visible: boolean; initial: string[]; onSave: (keys: string[]) => void }) {
  const [sel, setSel] = useState<string[]>(props.initial);
  useEffect(() => { if (props.visible) setSel(props.initial); }, [props.visible]); // eslint-disable-line react-hooks/exhaustive-deps
  const toggle = (k: string) => setSel((p) => (p.includes(k) ? p.filter((x) => x !== k) : [...p, k]));
  return (
    <Sheet visible={props.visible} onClose={() => props.onSave(sel)} title="What do you like?">
      <Text style={styles.todayDate}>Pick a few. We will show them first on the Today screen. You can change it any time.</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {INTEREST_KEYS.map((k) => (
          <Chip key={k} label={cat(k).label} active={sel.includes(k)} color={cat(k).accent} onPress={() => toggle(k)} />
        ))}
      </View>
      <BigButton label={sel.length ? 'Done' : 'Skip'} icon="checkmark" onPress={() => props.onSave(sel)} />
    </Sheet>
  );
}

function SearchScreen(props: {
  visible: boolean; onClose: () => void; query: string; setQuery: (q: string) => void;
  items: Item[]; city: string; card: (i: Item) => React.ReactNode; jump: Jump; detail: React.ReactNode;
}) {
  const shortcuts: Shortcut[] = shortcutsFor(props.query);
  // Wyszukiwarka szuka w całej bazie: najpierw wybrane miasto (bez filtra dzielnic), potem reszta ZEA z nazwą miasta.
  const results = sortItems(searchItems(props.items, props.query), 'default');
  const here = results.filter((i) => i.city === props.city);
  const elsewhere = results
    .filter((i) => i.city !== props.city)
    .map((i) => ({ ...i, where: i.where && !i.where.includes(i.city) ? `${i.where}, ${i.city}` : i.city }));
  const groups: [string, Item[]][] = [
    ['Events', here.filter((i) => i.kind === 'event')],
    ['Places', here.filter((i) => i.kind === 'place')],
    ['Deals', here.filter((i) => i.kind === 'deal')],
    ['Elsewhere in the UAE', elsewhere],
  ];
  const go = (s: Shortcut) => props.jump({ tab: s.tab, key: s.key, day: s.tab === 'events' ? 'all' : undefined, dealDay: s.tab === 'deals' ? null : undefined });
  return (
    <Modal visible={props.visible} animationType="slide" onRequestClose={props.onClose}>
      <SafeAreaProvider>
        <SafeAreaView style={styles.screen}>
          <View style={styles.searchBar}>
            <Ionicons name="search" size={18} color={colors.muted} />
            <TextInput
              autoFocus value={props.query} onChangeText={props.setQuery} placeholder="Search events, places, deals"
              placeholderTextColor={colors.muted} style={styles.searchInput} returnKeyType="search" autoCorrect={false}
              onSubmitEditing={() => { if (shortcuts.length > 0) go(shortcuts[0]); }}
            />
            <Pressable onPress={props.onClose} hitSlop={10}>
              <Text style={styles.seeAll}>Cancel</Text>
            </Pressable>
          </View>
          <ScrollView contentContainerStyle={styles.list} keyboardShouldPersistTaps="handled">
            {shortcuts.map((s) => (
              <Pressable key={`${s.tab}:${s.key}`} onPress={() => go(s)} style={styles.shortcut}>
                <Ionicons name="arrow-forward-circle" size={22} color={colors.primary} />
                <Text style={styles.shortcutText}>Go to {s.label}</Text>
              </Pressable>
            ))}
            {props.query.trim().length < 2 ? (
              <Empty text={'Try "brunch", "day pass", "beach" or a venue name.'} />
            ) : results.length === 0 && shortcuts.length === 0 ? (
              <Empty text="No matches. Check the spelling or try a shorter word." />
            ) : (
              groups.filter(([, g]) => g.length > 0).map(([name, g]) => (
                <View key={name}>
                  <Text style={[styles.secTitle, { marginVertical: 8 }]}>{name} ({g.length})</Text>
                  {g.slice(0, 20).map(props.card)}
                </View>
              ))
            )}
          </ScrollView>
          {props.detail}
        </SafeAreaView>
      </SafeAreaProvider>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 6, paddingBottom: 10 },
  brand: { color: colors.text, fontSize: 26, fontWeight: '800' },
  where: { flexDirection: 'row', alignItems: 'center', marginTop: 2 },
  whereText: { color: colors.primary, fontSize: 15, fontWeight: '600', marginHorizontal: 4, flexShrink: 1 },
  headBtn: { marginLeft: 18, padding: 4 },
  errorBox: { backgroundColor: colors.errorBg, marginHorizontal: 16, marginBottom: 8, padding: 10, borderRadius: 10 },
  newBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.chip, borderColor: colors.border, borderWidth: 1,
    marginHorizontal: 16, marginBottom: 8, paddingVertical: 10, paddingHorizontal: 14, borderRadius: 12,
  },
  newBannerText: { flex: 1, color: colors.text, fontSize: 15, fontWeight: '600' },
  errorText: { color: colors.errorText, fontSize: 13 },
  chipRow: { height: 50, flexGrow: 0, flexShrink: 0 },
  chipRowIn: { paddingHorizontal: 16, alignItems: 'flex-start' },
  toolbar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, marginBottom: 6 },
  tool: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.chip, borderColor: colors.border, borderWidth: 1,
    borderRadius: 18, paddingHorizontal: 13, paddingVertical: 8, marginRight: 8,
  },
  toolOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  toolText: { color: colors.text, fontSize: 14, marginLeft: 5 },
  count: { color: colors.muted, fontSize: 13 },
  activeCat: { color: colors.muted, fontSize: 13, paddingHorizontal: 16, marginBottom: 6 },
  list: { paddingHorizontal: 16, paddingBottom: 24, paddingTop: 4 },
  tabBar: { flexDirection: 'row', backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.border },
  tabBtn: { flex: 1, alignItems: 'center', paddingTop: 5, paddingBottom: 6 },
  tabText: { color: colors.muted, fontSize: 12, marginTop: 2 },
  section: { color: colors.muted, fontSize: 13, fontWeight: '700', marginTop: 10, marginBottom: 8, textTransform: 'uppercase' },
  wrap: { flexDirection: 'row', flexWrap: 'wrap' },
  hint: { color: colors.muted, fontSize: 12, marginBottom: 4 },
  todayDate: { color: colors.muted, fontSize: 14, marginBottom: 10 },
  chipSep: { width: 1, alignSelf: 'stretch', backgroundColor: colors.border, marginHorizontal: 6, marginVertical: 6 },
  secHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 },
  secTitle: { color: colors.text, fontSize: 20, fontWeight: '800' },
  seeAll: { color: colors.primary, fontSize: 14, fontWeight: '600' },
  searchBar: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface, margin: 16, marginBottom: 6,
    borderRadius: 14, paddingHorizontal: 12, borderWidth: 1, borderColor: colors.border,
  },
  searchInput: { flex: 1, color: colors.text, fontSize: 16, paddingVertical: 12, marginHorizontal: 8 },
  shortcut: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.chip, borderRadius: 14, padding: 14,
    marginBottom: 10, borderWidth: 1, borderColor: colors.primary,
  },
  shortcutText: { color: colors.text, fontSize: 16, fontWeight: '700', marginLeft: 10 },
});
