import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { Linking, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { sendSuggestion } from './api';
import { REPORT_EMAIL } from './config';
import { IconName } from './logic';
import { colors } from './theme';
import { Sheet } from './ui';

const PRIVACY_URL = 'https://outtodayapp.github.io/privacy.html';
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
      <Feedback />
      <Row icon="mail-outline" label="Email us"
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

// Błąd / uwaga z apki -> tabela suggestions (tytuł "Feedback: ..."), czytane w porannym mailu i przez Claude.
function Feedback() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [contact, setContact] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const send = () => {
    if (!text.trim()) return;
    setState('sending');
    sendSuggestion({
      title: `Feedback: ${text.trim().replace(/\s+/g, ' ')}`.slice(0, 150),
      note: `${text.trim()}\n\n[${Platform.OS} ${String(Platform.Version)} · app ${VERSION}]`,
      contact: contact || undefined,
    }).then(() => { setState('sent'); setText(''); }).catch(() => setState('error'));
  };
  if (!open) return <Row icon="bug-outline" label="Send feedback / report a bug" onPress={() => { setOpen(true); setState('idle'); }} />;
  return (
    <View style={styles.fb}>
      <Text style={styles.fbTitle}>Send feedback / report a bug</Text>
      {state === 'sent' ? (
        <Text style={styles.p}>Thank you! We got it.</Text>
      ) : (
        <>
          <TextInput style={[styles.input, { minHeight: 90 }]} multiline value={text} onChangeText={setText}
            placeholder="What went wrong or what would you change? (which screen, which event...)" placeholderTextColor={colors.muted} />
          <TextInput style={styles.input} value={contact} onChangeText={setContact} autoCapitalize="none"
            placeholder="Your name or email (optional)" placeholderTextColor={colors.muted} />
          {state === 'error' && <Text style={styles.err}>Could not send. Check your connection and try again.</Text>}
          <Pressable onPress={send} disabled={state === 'sending' || !text.trim()}
            style={[styles.btn, (!text.trim() || state === 'sending') && { opacity: 0.5 }]}>
            <Text style={styles.btnText}>{state === 'sending' ? 'Sending...' : 'Send'}</Text>
          </Pressable>
        </>
      )}
    </View>
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
  fb: { borderTopWidth: 1, borderTopColor: colors.border, paddingVertical: 12 },
  fbTitle: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 8 },
  input: { color: colors.text, fontSize: 15, borderWidth: 1, borderColor: colors.border, borderRadius: 10, padding: 10, marginBottom: 8, textAlignVertical: 'top' },
  err: { color: '#FF8A8A', fontSize: 13, marginBottom: 8 },
  btn: { backgroundColor: colors.primary, borderRadius: 10, paddingVertical: 11, alignItems: 'center' },
  btnText: { color: '#0D1B33', fontSize: 16, fontWeight: '700' },
  note: { color: colors.muted, fontSize: 12, marginTop: 12, lineHeight: 17 },
});
