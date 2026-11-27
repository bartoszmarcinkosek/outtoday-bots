// Gdy ekran się wysypie: zamiast białego ekranu – prośba o ponowne uruchomienie + automatyczne zgłoszenie błędu.
import React from 'react';
import { Pressable, Text, View } from 'react-native';
import * as Updates from 'expo-updates';
import { reportError } from './errors';

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: unknown, info: { componentStack?: string | null }) {
    reportError('screen', error, (info.componentStack ?? '').split('\n').slice(0, 8).join('\n'));
  }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <View style={{ flex: 1, backgroundColor: '#0D1B33', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
        <Text style={{ color: '#EAF1FF', fontSize: 20, fontWeight: '700', marginBottom: 10, textAlign: 'center' }}>Something went wrong</Text>
        <Text style={{ color: '#9FB3D9', fontSize: 15, marginBottom: 24, textAlign: 'center' }}>We have been notified and will fix it. Please reopen the app.</Text>
        <Pressable onPress={() => { Updates.reloadAsync().catch(() => this.setState({ failed: false })); }}
          style={{ backgroundColor: '#8FB4FF', paddingVertical: 12, paddingHorizontal: 28, borderRadius: 12 }}>
          <Text style={{ color: '#0D1B33', fontWeight: '700', fontSize: 16 }}>Reload</Text>
        </Pressable>
      </View>
    );
  }
}
