import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import { StatusBar } from 'expo-status-bar';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator, FlatList, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { AppData, fetchAll, loadCached } from './src/api';
import { DOW_CHIPS, fmtDate, inRange, rangeFor } from './src/dates';
import {
  Item, SORT_LABEL, Shortcut, SortKey, buildItems, dealEndedToday, dealOnDay, dealOnNow, searchItems, shortcutsFor, sortItems, todayIso,
  placeOpen,
} from './src/logic';
import { ZoneMap } from './src/map';
import { SuggestSheet } from './src/suggest';
import { AboutSheet } from './src/about';
import { BigButton, CalendarSheet, DetailSheet, LocationSheet } from './src/sheets';
import { cat, colors, dealStyle } from './src/theme';
import { Chip, Empty, ItemCard, Sheet } from './src/ui';
import { hasTop10 } from './src/top10';
import { CITY_CENTER, ZONES, distanceKm } from './src/zones';

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
const USAGE_KEY = 'outtoday.filterUse.v1';
const KIND_OF: Record<ListTab, Item['kind']> = { events: 'event', places: 'place', deals: 'deal' };

export default function App() {
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
  const [cats, setCats] = useState<Record<ListTab, string | null>>({ events: null, places: null, deals: null });
  const [sorts, setSorts] = useState<Record<ListTab, SortKey>>({ events: 'default', places: 'default', deals: 'default' });
  const [free, setFree] = useState(false);
  const [kid, setKid] = useState(false);
  const [pet, setPet] = useState(false);
  const [ladies, setLadies] = useState(false);
  const [inOut, setInOut] = useState<InOut>('all');
  const [cap, setCap] = useState<number | null>(null);

  // Okna
  const [selected, setSelected] = useState<Item | null>(null);
  const [showWhere, setShowWhere] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showCal, setShowCal] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
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
  const toggleFav = (key: string) => {
    setFavs((prev) => {
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

  const listFor = useCallback(
    (t: ListTab): Item[] => {
      const range = rangeFor(day);
      // Top 10 zawsze dla całego miasta, niezależnie od wybranego obszaru.
      const base = t === 'places' && topOnly && hasTop10(city) ? all.filter((i) => i.city === city) : local;
      const filtered = base
        .filter((i) => i.kind === KIND_OF[t])
        .filter((i) => !cats[t] || i.catKey === cats[t])
        .filter((i) => !free || i.free)
        .filter((i) => !kid || i.kid)
        .filter((i) => !pet || i.pet)
        .filter((i) => !ladies || i.ladies)
        .filter((i) => t !== 'events' || inRange(i.event!, range))
        .filter((i) => t !== 'places' || inOut === 'all' || i.indoor === (inOut === 'in'))
        .filter((i) => t !== 'places' || !topOnly || !hasTop10(city) || i.top != null)
        .filter((i) => t !== 'places' || !openOnly || placeOpen(i.place)?.open === true)
        .filter((i) => t !== 'deals' || dealDay === null || dealOnDay(i.deal!, dealDay))
        .filter((i) => t !== 'deals' || cap === null || (i.price !== null && i.price <= cap));
      if (t === 'places' && topOnly && hasTop10(city) && sorts[t] === 'default') return [...filtered].sort((a, b) => (a.top ?? 99) - (b.top ?? 99));
      return sortItems(filtered, sorts[t]);
    },
    [local, all, cats, free, kid, pet, ladies, day, inOut, dealDay, cap, sorts, topOnly, openOnly, city],
  );

  const list = useMemo(() => (tab === 'today' ? [] : listFor(tab)), [tab, listFor]);

  const catKeys = useMemo(() => {
    if (tab === 'today') return [];
    const present = new Set(local.filter((i) => i.kind === KIND_OF[tab]).map((i) => i.catKey));
    const lbl = (k: string) => (tab === 'deals' ? dealStyle(k) : cat(k)).label;
    return [...present].filter(Boolean).sort((a, b) => lbl(a).localeCompare(lbl(b)));
  }, [tab, local]);

  const activeCount =
    Number(free) + Number(kid) + Number(pet) + Number(ladies) +
    (tab !== 'today' && cats[tab] ? 1 : 0) + (tab === 'places' && inOut !== 'all' ? 1 : 0) + (tab === 'places' && topOnly ? 1 : 0) + (tab === 'places' && openOnly ? 1 : 0) +
    (tab === 'deals' && cap !== null ? 1 : 0);

  const clearFilters = () => {
    setFree(false); setKid(false); setPet(false); setLadies(false); setInOut('all'); setCap(null); setTopOnly(false); setOpenOnly(false);
    setCats({ events: null, places: null, deals: null });
  };

  // Przejście z ekranu Today albo z wyszukiwarki do gotowej listy.
  const jump = (s: { tab: ListTab; key?: string | null; day?: string; dealDay?: number | null; free?: boolean }) => {
    clearFilters();
    setCats({ events: null, places: null, deals: null, [s.tab]: s.key ?? null } as Record<ListTab, string | null>);
    if (s.day) setDay(s.day);
    if (s.dealDay !== undefined) setDealDay(s.dealDay);
    if (s.free) setFree(true);
    setShowSearch(false);
    setQuery('');
    setTab(s.tab);
  };

  const whereLabel = zones.length === 0
    ? city
    : `${city} · ${zones.map((z) => ZONES.find((x) => x.key === z)?.label ?? z).join(', ')}`;
  const isDate = /^\d{4}-\d{2}-\d{2}$/.test(day);
  const labelFor = (t: ListTab, key: string) => (t === 'deals' ? dealStyle(key) : cat(key));
  const card = (item: Item) => (
    <ItemCard key={item.key} item={item} fav={favs.includes(item.key)} onFav={() => toggleFav(item.key)} onPress={() => setSelected(item)} />
  );
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

      {!data ? (
        <ActivityIndicator color={colors.primary} style={{ marginTop: 60 }} />
      ) : tab === 'today' ? (
        <TodayScreen local={local} card={card} jump={jump} refreshControl={refreshControl} />
      ) : (
        <>
          {tab === 'events' && (
            <View style={styles.chipRow}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRowIn}>
              {DAY_CHIPS.map((d) => (
                <Chip key={d.key} label={d.label} active={day === d.key} onPress={() => setDay(d.key)} />
              ))}
              <Chip label={isDate ? fmtDate(day) : 'Pick a date'} icon="calendar-outline" active={isDate} onPress={() => setShowCal(true)} />
            </ScrollView>
            </View>
          )}
          {tab === 'places' && (
            <View style={styles.chipRow}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRowIn}>
              <Chip label="All places" active={!topOnly && !openOnly} onPress={() => { setTopOnly(false); setOpenOnly(false); }} />
              <Chip label="Open now" icon="time-outline" active={openOnly} onPress={() => setOpenOnly(!openOnly)} />
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
            <Pressable onPress={() => setView(view === 'list' ? 'map' : 'list')} style={styles.tool}>
              <Ionicons name={view === 'list' ? 'map-outline' : 'list-outline'} size={19} color={colors.text} />
              <Text style={styles.toolText}>{view === 'list' ? 'Map' : 'List'}</Text>
            </Pressable>
            <View style={{ flex: 1 }} />
            <Text style={styles.count}>{list.length} {list.length === 1 ? 'result' : 'results'}</Text>
          </View>
          {cats[tab] && (
            <Text style={styles.activeCat}>Showing: {labelFor(tab, cats[tab]!).label}</Text>
          )}

          {view === 'map' ? (
            <ZoneMap items={list} city={city} card={card} />
          ) : (
            <FlatList
              data={list}
              keyExtractor={(i) => i.key}
              renderItem={({ item }) => card(item)}
              contentContainerStyle={styles.list}
              refreshControl={refreshControl}
              ListEmptyComponent={<Empty text="Nothing matches these filters. Try another day, area or fewer filters." />}
            />
          )}
        </>
      )}

      <SafeAreaView edges={['bottom']} style={styles.tabBar}>
        {TABS.map((t) => (
          <Pressable key={t.key} style={styles.tabBtn} onPress={() => { setTab(t.key); setView('list'); }}>
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

          {tab === 'deals' && (
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
                <Chip key={k} label={c.label} color={c.accent} active={cats[tab] === k}
                  onPress={() => {
                    if (cats[tab] !== k) bump(`${tab}:${k}`);
                    setCats({ ...cats, [tab]: cats[tab] === k ? null : k });
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
                  <Chip label="All" active={!cats[tab]} onPress={() => setCats({ ...cats, [tab]: null })} />
                  {rest.map(chip)}
                </View>
              </>
            );
          })()}
          {activeCount > 0 && <BigButton label="Clear all filters" quiet onPress={clearFilters} />}
        </Sheet>
      )}

      <SearchScreen visible={showSearch} onClose={() => { setShowSearch(false); setQuery(''); }} query={query} setQuery={setQuery}
        items={all.filter((i) => i.city === city)} card={card} jump={jump}
        detail={
          <DetailSheet item={showSearch ? selected : null} fav={!!selected && favs.includes(selected.key)}
            onFav={() => selected && toggleFav(selected.key)} onClose={() => setSelected(null)} />
        } />

      <AboutSheet visible={showAbout} onClose={() => setShowAbout(false)} onSuggest={() => setShowSuggest(true)} />
      <SuggestSheet visible={showSuggest} onClose={() => setShowSuggest(false)} city={city} />
      <Modal visible={showFavs} animationType="slide" onRequestClose={() => setShowFavs(false)}>
        <SafeAreaProvider>
          <SafeAreaView style={styles.screen}>
            <View style={styles.header}>
              <Text style={[styles.brand, { flex: 1 }]}>Saved</Text>
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
              onFav={() => selected && toggleFav(selected.key)} onClose={() => setSelected(null)} />
          </SafeAreaView>
        </SafeAreaProvider>
      </Modal>

      <DetailSheet item={showFavs || showSearch ? null : selected} fav={!!selected && favs.includes(selected.key)}
        onFav={() => selected && toggleFav(selected.key)} onClose={() => setSelected(null)} />
    </SafeAreaView>
  );
}

type Jump = (s: { tab: ListTab; key?: string | null; day?: string; dealDay?: number | null; free?: boolean }) => void;

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
function TodayScreen(props: { local: Item[]; card: (i: Item) => React.ReactNode; jump: Jump; refreshControl: React.ReactElement<any> }) {
  const now = new Date();
  const today = todayIso(now);
  const range: [string, string] = [today, today];
  const events = sortItems(props.local.filter((i) => i.event && inRange(i.event, range)), 'default');
  const single = events.filter((i) => !i.endsSoon && i.event!.start_date === today);
  const onToday = rankToday([...single, ...events.filter((i) => !single.includes(i))], now);
  const freeToday = onToday.filter((i) => i.free);
  const deals = props.local.filter((i) => i.deal && dealOnDay(i.deal, now.getDay()));
  const rank = (i: Item) => (dealOnNow(i.deal!, now) ? 0 : dealEndedToday(i.deal!, now) ? 2 : 1);
  const dealsSorted = sortItems(deals, 'default').sort((a, b) => rank(a) - rank(b));
  const ending = sortItems(props.local.filter((i) => i.kind === 'event' && i.endsSoon), 'default');
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
    section('On today', onToday, 5, () => props.jump({ tab: 'events', day: 'today' })),
    section('This weekend', weekend, 5, () => props.jump({ tab: 'events', day: 'weekend' })),
    section('Free today', freeToday, 4, () => props.jump({ tab: 'events', day: 'today', free: true })),
    section('Deals today', dealsSorted, 5, () => props.jump({ tab: 'deals', dealDay: now.getDay() })),
    section('Ends soon', ending, 4, () => props.jump({ tab: 'events', day: 'all' })),
  ].filter(Boolean);

  return (
    <ScrollView contentContainerStyle={styles.list} refreshControl={props.refreshControl}>
      <Text style={styles.todayDate}>{fmtDate(today)}</Text>
      {blocks.length > 0 ? blocks : <Empty text="Nothing listed for today in this area. Try a wider area or check the Events tab." />}
    </ScrollView>
  );
}

function SearchScreen(props: {
  visible: boolean; onClose: () => void; query: string; setQuery: (q: string) => void;
  items: Item[]; card: (i: Item) => React.ReactNode; jump: Jump; detail: React.ReactNode;
}) {
  const shortcuts: Shortcut[] = shortcutsFor(props.query);
  const results = sortItems(searchItems(props.items, props.query), 'default');
  const groups: [string, Item[]][] = [
    ['Events', results.filter((i) => i.kind === 'event')],
    ['Places', results.filter((i) => i.kind === 'place')],
    ['Deals', results.filter((i) => i.kind === 'deal')],
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
