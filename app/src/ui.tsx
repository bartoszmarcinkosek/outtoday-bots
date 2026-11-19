import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Image, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { IconName, Item, dealEndedToday, dealOnDay, dealOnNow, placeOpen } from './logic';
import { colors } from './theme';

export function Chip(props: { label: string; active: boolean; onPress: () => void; color?: string; icon?: IconName }) {
  const tint = props.color ?? colors.primary;
  return (
    <Pressable
      onPress={props.onPress}
      style={[styles.chip, props.active && { backgroundColor: tint, borderColor: tint }]}
    >
      {props.icon && (
        <Ionicons name={props.icon} size={16} color={props.active ? colors.bg : colors.muted} style={{ marginRight: 5 }} />
      )}
      <Text style={[styles.chipText, props.active && { color: colors.bg, fontWeight: '700' }]}>{props.label}</Text>
    </Pressable>
  );
}

export function Pill(props: { text: string; color: string; solid?: boolean }) {
  return (
    <View style={[styles.pill, props.solid ? { backgroundColor: props.color } : { borderColor: props.color, borderWidth: 1 }]}>
      <Text style={[styles.pillText, { color: props.solid ? colors.bg : props.color }]}>{props.text}</Text>
    </View>
  );
}

// Etykiety stanu: co trwa teraz, co się kończy, co jest nowe.
export function badgesFor(item: Item, now: Date = new Date()): string[] {
  const out: string[] = [];
  if (item.deal) {
    if (dealOnNow(item.deal, now)) out.push('On now');
    else if (dealOnDay(item.deal, now.getDay()) && !dealEndedToday(item.deal, now)) out.push('On today');
  }
  if (item.place) {
    const o = placeOpen(item.place, now);
    if (o?.open) out.push(o.until ? `Open till ${o.until}` : 'Open 24h');
  }
  if (item.endsSoon) out.push('Ends soon');
  if (item.isNew) out.push('New');
  return out;
}

export function ItemCard(props: { item: Item; photo?: number | null; fav: boolean; onFav: () => void; onPress: () => void }) {
  const { item } = props;
  const c = item.look;
  const badges = badgesFor(item);
  const meta = [item.where, item.km != null ? `~${Math.max(1, Math.round(item.km))} km` : null].filter(Boolean).join(' · ');
  return (
    <Pressable onPress={props.onPress} style={[styles.card, { backgroundColor: c.card }]}>
      {props.photo ? (
        <View style={styles.photoBox}>
          <Image source={props.photo} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }} resizeMode="cover" />
        </View>
      ) : (
        <View style={[styles.iconBox, { backgroundColor: 'rgba(0,0,0,0.22)' }]}>
          <Ionicons name={item.icon} size={28} color={c.accent} />
        </View>
      )}
      <View style={{ flex: 1 }}>
        <View style={styles.pillRow}>
          {item.top != null && <Pill text={`TOP 10 · #${item.top}`} color="#FFD166" solid />}
          <Pill text={c.label} color={c.accent} />
          {item.free && <Pill text="FREE" color={colors.free} solid />}
          {badges.map((b) => (
            <Pill key={b} text={b} color={c.title} solid />
          ))}
        </View>
        <Text style={[styles.cardTitle, { color: c.title }]} numberOfLines={2}>
          {item.title}
        </Text>
        {!!item.when && (
          <Text style={[styles.cardSub, { color: c.sub }]} numberOfLines={2}>
            {item.when}
          </Text>
        )}
        {!!meta && (
          <Text style={[styles.cardSub, { color: c.sub }]} numberOfLines={1}>
            {meta}
          </Text>
        )}
        {!!item.priceText && !item.free && (
          <Text style={[styles.cardPrice, { color: c.title }]} numberOfLines={1}>
            {item.priceText}
          </Text>
        )}
      </View>
      <Pressable onPress={props.onFav} hitSlop={12} style={styles.heart}>
        <Ionicons name={props.fav ? 'heart' : 'heart-outline'} size={26} color={props.fav ? '#FF8FA3' : c.sub} />
      </Pressable>
    </Pressable>
  );
}

// Wysuwany od dołu panel na filtry, wybór miasta, kalendarz i szczegóły.
export function Sheet(props: { visible: boolean; onClose: () => void; title?: string; children: React.ReactNode; footer?: React.ReactNode }) {
  return (
    <Modal visible={props.visible} transparent animationType="slide" onRequestClose={props.onClose}>
      <View style={styles.backdrop}>
        <Pressable style={{ flex: 1 }} onPress={props.onClose} />
        <View style={styles.sheet}>
          <View style={styles.sheetHead}>
            <Text style={styles.sheetTitle}>{props.title ?? ''}</Text>
            <Pressable onPress={props.onClose} hitSlop={12}>
              <Ionicons name="close" size={24} color={colors.muted} />
            </Pressable>
          </View>
          <ScrollView contentContainerStyle={{ paddingBottom: 16 }} keyboardShouldPersistTaps="handled">
            {props.children}
          </ScrollView>
          {props.footer}
        </View>
      </View>
    </Modal>
  );
}

export function Empty(props: { text: string }) {
  return <Text style={styles.empty}>{props.text}</Text>;
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row', alignItems: 'center', paddingHorizontal: 13, paddingVertical: 8, borderRadius: 18,
    backgroundColor: colors.chip, borderWidth: 1, borderColor: colors.border, marginRight: 8, marginBottom: 8,
  },
  chipText: { color: colors.text, fontSize: 14 },
  pill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 9, marginRight: 6, marginBottom: 4 },
  pillText: { fontSize: 11, fontWeight: '700' },
  pillRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 4, paddingRight: 26 },
  card: { flexDirection: 'row', borderRadius: 16, padding: 14, marginBottom: 12 },
  iconBox: { width: 42, minHeight: 42, alignSelf: 'stretch', borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  // zdjęcie kategorii: o 25% szersze niż ikonka (42 → 53), zawsze ta sama wysokość (2:3)
  photoBox: { width: 53, height: 80, borderRadius: 12, marginRight: 12, overflow: 'hidden', backgroundColor: 'rgba(0,0,0,0.22)' },
  cardTitle: { fontSize: 17, fontWeight: '700', marginBottom: 3 },
  cardSub: { fontSize: 13, marginTop: 1 },
  cardPrice: { fontSize: 13, fontWeight: '600', marginTop: 5 },
  heart: { position: 'absolute', top: 12, right: 12 },
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.55)' },
  sheet: {
    backgroundColor: colors.surface, borderTopLeftRadius: 22, borderTopRightRadius: 22,
    paddingHorizontal: 18, paddingTop: 14, paddingBottom: 26, maxHeight: '88%',
  },
  sheetHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sheetTitle: { color: colors.text, fontSize: 19, fontWeight: '700', flex: 1, paddingRight: 12 },
  empty: { color: colors.muted, textAlign: 'center', marginTop: 36, fontSize: 15, paddingHorizontal: 24 },
});
