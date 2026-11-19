import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { sendSuggestion } from './api';
import { colors } from './theme';
import { Chip, Sheet } from './ui';
import { CITIES } from './zones';

// "Suggest an event": formularz zgłoszenia. Zgłoszenie trafia do porannego e-maila, sprawdzamy je przed dodaniem.
export function SuggestSheet(props: { visible: boolean; onClose: () => void; city: string }) {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [venue, setVenue] = useState('');
  const [city, setCity] = useState(props.city);
  const [price, setPrice] = useState('');
  const [link, setLink] = useState('');
  const [note, setNote] = useState('');
  const [contact, setContact] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle');

  const ok = title.trim().length >= 3 && (date.trim() || link.trim());
  const close = () => {
    if (state === 'done') {
      setTitle(''); setDate(''); setVenue(''); setPrice(''); setLink(''); setNote(''); setContact(''); setState('idle');
    }
    props.onClose();
  };
  const send = async () => {
    if (!ok || state === 'sending') return;
    setState('sending');
    try {
      // cena idzie w polu note (bez zmiany bazy) – w porannym e-mailu widać ją na początku notatki
      const fullNote = [price.trim() && `Price: ${price.trim()}`, note.trim()].filter(Boolean).join('\n');
      await sendSuggestion({ title, event_date: date, venue, city, link, note: fullNote, contact });
      setState('done');
    } catch {
      setState('error');
    }
  };

  return (
    <Sheet visible={props.visible} onClose={close} title="Suggest an event">
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        {state === 'done' ? (
          <View style={styles.done}>
            <Ionicons name="checkmark-circle" size={48} color={colors.free} />
            <Text style={styles.doneTitle}>Thank you!</Text>
            <Text style={styles.hint}>We check every suggestion against the official page before it goes live.</Text>
            <Pressable onPress={close} style={styles.btn}><Text style={styles.btnText}>Close</Text></Pressable>
          </View>
        ) : (
          <>
            <Text style={styles.hint}>Know an event, offer or class we are missing? Tell us and we will check it.</Text>
            <Field label="What is it? *" value={title} onChange={setTitle} placeholder="e.g. Sunset yoga on the beach" max={150} />
            <Field label="When?" value={date} onChange={setDate} placeholder="e.g. Sat 28 Nov, 6 pm" max={40} />
            <Field label="Where?" value={venue} onChange={setVenue} placeholder="Venue or area" max={150} />
            <Field label="Price" value={price} onChange={setPrice} placeholder="e.g. Free, AED 50, from AED 99" max={80} />
            <Text style={styles.label}>City</Text>
            <View style={styles.chips}>
              {CITIES.map((c) => <Chip key={c} label={c} active={city === c} onPress={() => setCity(c)} />)}
            </View>
            <Field label="Link (official page, tickets or Instagram)" value={link} onChange={setLink} placeholder="https://" max={400} url />
            <Field label="Anything else?" value={note} onChange={setNote} placeholder="Who it is for, how to book..." max={600} multi />
            <Field label="Your email (optional, only if we have questions)" value={contact} onChange={setContact} placeholder="name@example.com" max={120} email />
            {state === 'error' && <Text style={styles.err}>Could not send. Check your connection and try again.</Text>}
            {!ok && <Text style={styles.small}>Add a name and either a date or a link.</Text>}
            <Pressable onPress={send} style={[styles.btn, !ok && styles.btnOff]} disabled={!ok}>
              {state === 'sending' ? <ActivityIndicator color={colors.bg} /> : <Text style={styles.btnText}>Send suggestion</Text>}
            </Pressable>
          </>
        )}
      </KeyboardAvoidingView>
    </Sheet>
  );
}

function Field(props: {
  label: string; value: string; onChange: (v: string) => void; placeholder: string; max: number;
  multi?: boolean; url?: boolean; email?: boolean;
}) {
  return (
    <View style={{ marginTop: 10 }}>
      <Text style={styles.label}>{props.label}</Text>
      <TextInput
        value={props.value} onChangeText={props.onChange} placeholder={props.placeholder} placeholderTextColor={colors.muted}
        maxLength={props.max} multiline={props.multi} style={[styles.input, props.multi && { height: 80, textAlignVertical: 'top' }]}
        autoCapitalize={props.url || props.email ? 'none' : 'sentences'} autoCorrect={!(props.url || props.email)}
        keyboardType={props.url ? 'url' : props.email ? 'email-address' : 'default'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  hint: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  label: { color: colors.muted, fontSize: 13, fontWeight: '700', marginBottom: 5, marginTop: 6 },
  input: {
    backgroundColor: colors.chip, borderColor: colors.border, borderWidth: 1, borderRadius: 12,
    color: colors.text, fontSize: 15, paddingHorizontal: 12, paddingVertical: 10,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  btn: { backgroundColor: colors.primary, borderRadius: 14, paddingVertical: 14, alignItems: 'center', marginTop: 16 },
  btnOff: { opacity: 0.4 },
  btnText: { color: colors.bg, fontSize: 16, fontWeight: '700' },
  err: { color: colors.errorText, marginTop: 10 },
  small: { color: colors.muted, fontSize: 12, marginTop: 10 },
  done: { alignItems: 'center', paddingVertical: 20 },
  doneTitle: { color: colors.text, fontSize: 20, fontWeight: '700', marginVertical: 8 },
});
