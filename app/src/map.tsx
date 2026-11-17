import React, { useMemo, useState } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import { Item } from './logic';
import { colors } from './theme';
import { Empty } from './ui';
import { CITY_CENTER, ZONES, ZONE_CENTER } from './zones';

// Mapa: dokładna pinezka dla każdego miejsca ze współrzędnymi; reszta zbiorczo jako pinezka dzielnicy.
export function ZoneMap(props: { items: Item[]; city: string; card: (i: Item) => React.ReactNode }) {
  const [picked, setPicked] = useState<string | null>(null);
  const [pickedItem, setPickedItem] = useState<string | null>(null);
  const exact = useMemo(() => props.items.filter((i) => i.geo).slice(0, 400), [props.items]);

  const counts = useMemo(() => {
    const out: Record<string, number> = {};
    for (const i of props.items) if (i.zone && !i.geo) out[i.zone] = (out[i.zone] ?? 0) + 1;
    return out;
  }, [props.items]);

  const zones = ZONES.filter((z) => counts[z.key] && ZONE_CENTER[z.key]);
  const noZone = props.items.filter((i) => !i.zone && !i.geo).length;
  const [lat, lng, zoom] = CITY_CENTER[props.city] ?? CITY_CENTER['Abu Dhabi'];
  const region = { latitude: lat, longitude: lng, latitudeDelta: zoom, longitudeDelta: zoom };
  const list = pickedItem ? props.items.filter((i) => i.key === pickedItem)
    : picked ? props.items.filter((i) => i.zone === picked && !i.geo) : [];
  const pickedLabel = ZONES.find((z) => z.key === picked)?.label;

  return (
    <View style={{ flex: 1 }}>
      <MapView key={props.city} style={styles.map} initialRegion={region} showsUserLocation userInterfaceStyle="dark"
        onPress={() => { setPicked(null); setPickedItem(null); }}>
        {exact.map((i) => (
          <Marker key={i.key} coordinate={{ latitude: i.geo![0], longitude: i.geo![1] }} tracksViewChanges={false}
            onPress={(e) => { e.stopPropagation(); setPicked(null); setPickedItem(i.key); }}>
            <View style={[styles.dot, pickedItem === i.key && styles.dotOn]} />
          </Marker>
        ))}
        {zones.map((z) => (
          <Marker key={z.key} coordinate={{ latitude: ZONE_CENTER[z.key][0], longitude: ZONE_CENTER[z.key][1] }}
            onPress={(e) => { e.stopPropagation(); setPickedItem(null); setPicked(z.key); }}>
            <View style={[styles.pin, picked === z.key && styles.pinOn]}>
              <Text style={[styles.pinCount, picked === z.key && { color: colors.bg }]}>{counts[z.key]}</Text>
              <Text style={[styles.pinLabel, picked === z.key && { color: colors.bg }]} numberOfLines={1}>{z.label}</Text>
            </View>
          </Marker>
        ))}
      </MapView>
      {picked || pickedItem ? (
        <FlatList
          data={list}
          keyExtractor={(i) => i.key}
          renderItem={({ item }) => <>{props.card(item)}</>}
          contentContainerStyle={styles.list}
          ListHeaderComponent={pickedItem ? undefined : <Text style={styles.head}>{pickedLabel} · {list.length}</Text>}
        />
      ) : (
        <View style={styles.list}>
          <Empty text={`Tap a pin to see what's there.${noZone ? ` ${noZone} without a known area are only in the list.` : ''}`} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  dot: { width: 14, height: 14, borderRadius: 7, backgroundColor: colors.primary, borderWidth: 2, borderColor: colors.bg },
  dotOn: { width: 20, height: 20, borderRadius: 10, backgroundColor: colors.text },
  map: { height: '48%', width: '100%' },
  pin: {
    backgroundColor: colors.surface, borderColor: colors.primary, borderWidth: 2, borderRadius: 14,
    paddingHorizontal: 8, paddingVertical: 4, alignItems: 'center', maxWidth: 130,
  },
  pinOn: { backgroundColor: colors.primary },
  pinCount: { color: colors.text, fontSize: 15, fontWeight: '800' },
  pinLabel: { color: colors.muted, fontSize: 10 },
  list: { paddingHorizontal: 16, paddingTop: 10, paddingBottom: 24 },
  head: { color: colors.text, fontSize: 18, fontWeight: '800', marginBottom: 10 },
});
