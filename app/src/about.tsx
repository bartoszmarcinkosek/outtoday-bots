import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { REPORT_EMAIL } from './config';
import { IconName } from './logic';
import { colors } from './theme';
import { Sheet } from './ui';

const PRIVACY_URL = 'https://bartoszmarcinkosek.github.io/outtoday-web/privacy.html';
const VERSION = '1.0.0';

// Ekran "About": czym jest apka, skąd dane, prywatność, kontakt.
export function AboutSheet(props: { visible: boolean; onClose: () => void; onSuggest: () => void }) {
  return (
    <Sheet visible={props.visible} onClose={props.onClose} title="About OutToday">
      <Text style={styles.p}>
        OutToday shows events, places and deals across all seven emirates, in one free app with no account and no ads.
      </Text>
      <Text style={styles.p}>
        Every listing comes from the venue's or organiser's official page, or from the official ticket seller. Dates, prices
        and times can change, so please check the official page before you go.
      </Text>
      <Row icon="add-circle-outline" label="Suggest an event" onPress={() => { props.onClose(); setTimeout(props.onSuggest, 450); }} />
      <Row icon="mail-outline" label="Contact us / report a problem"
        onPress={() => Linking.openURL(`mailto:${REPORT_EMAIL}?subject=${encodeURIComponent('OutToday feedback')}`)} />
      <Row icon="shield-checkmark-outline" label="Privacy policy" onPress={() => Linking.openURL(PRIVACY_URL)} />
      <Text style={styles.note}>
        For adults (21+): some listings mention venues and offers that serve alcohol. Your location and favourites stay on
        your phone.
      </Text>
      <Text style={styles.note}>
        Map locations: © OpenStreetMap contributors (openstreetmap.org/copyright), geocoding by Nominatim.
      </Text>
      <Text style={styles.note}>Version {VERSION} · {REPORT_EMAIL}</Text>
    </Sheet>
  );
}

function Row(props: { icon: IconName; label: string; onPress: () => void }) {
  return (
    <Pressable onPress={props.onPress} style={styles.row}>
      <Ionicons name={props.icon} size={22} color={colors.primary} />
      <Text style={styles.rowText}>{props.label}</Text>
      <Ionicons name="chevron-forward" size={18} color={colors.muted} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  p: { color: colors.text, fontSize: 15, lineHeight: 21, marginBottom: 10 },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: 13, borderTopWidth: 1, borderTopColor: colors.border },
  rowText: { color: colors.text, fontSize: 16, marginLeft: 12, flex: 1 },
  note: { color: colors.muted, fontSize: 12, marginTop: 12, lineHeight: 17 },
});
