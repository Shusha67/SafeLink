import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  Switch,
  Platform,
} from 'react-native';
import { useClipboardMonitor } from '../hooks/useClipboardMonitor';

export default function StatusScreen(): React.JSX.Element {
  const [monitorEnabled, setMonitorEnabled] = useState(true);

  if (monitorEnabled) {
    useClipboardMonitor();
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />

      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoCircle}>
            <Text style={styles.logoText}>🛡️</Text>
          </View>
        </View>

        {/* Title */}
        <Text style={styles.title}>SafeLink</Text>
        <Text style={styles.subtitle}>Link Safety Scanner</Text>

        {/* Status Card */}
        <View style={styles.card}>
          <View style={styles.statusRow}>
            <View style={styles.statusLeft}>
              <View style={[styles.dot, monitorEnabled ? styles.dotActive : styles.dotInactive]} />
              <Text style={styles.statusLabel}>
                {monitorEnabled ? 'Monitoring Active' : 'Monitoring Paused'}
              </Text>
            </View>
            <Switch
              value={monitorEnabled}
              onValueChange={setMonitorEnabled}
              trackColor={{ false: '#d1d5db', true: '#a5b4fc' }}
              thumbColor={monitorEnabled ? '#4f46e5' : '#9ca3af'}
            />
          </View>

          <View style={styles.divider} />

          <Text style={styles.instructions}>
            {monitorEnabled
              ? 'Copy any link on your phone.\nSafeLink will ask if you want to check it.'
              : 'Turn monitoring on to start\nchecking links automatically.'}
          </Text>
        </View>

        {/* How it works */}
        <View style={styles.stepsContainer}>
          <Text style={styles.stepsTitle}>How it works</Text>
          {[
            { num: '1', text: 'Copy a link from WhatsApp, SMS, or anywhere' },
            { num: '2', text: 'Tap "Yes, Check" on the notification' },
            { num: '3', text: 'See the result: 🟢 Safe, 🟡 Suspicious, or 🔴 Unsafe' },
          ].map((step) => (
            <View key={step.num} style={styles.stepRow}>
              <View style={styles.stepCircle}>
                <Text style={styles.stepNum}>{step.num}</Text>
              </View>
              <Text style={styles.stepText}>{step.text}</Text>
            </View>
          ))}
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'android' ? 48 : 24,
    alignItems: 'center',
  },
  logoContainer: {
    marginBottom: 16,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 36,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    marginBottom: 32,
  },
  card: {
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 32,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  dotActive: {
    backgroundColor: '#22c55e',
  },
  dotInactive: {
    backgroundColor: '#d1d5db',
  },
  statusLabel: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
  },
  divider: {
    height: 1,
    backgroundColor: '#f3f4f6',
    marginVertical: 16,
  },
  instructions: {
    fontSize: 15,
    color: '#6b7280',
    lineHeight: 22,
    textAlign: 'center',
  },
  stepsContainer: {
    width: '100%',
  },
  stepsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9ca3af',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 16,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 14,
  },
  stepCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#eef2ff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  stepNum: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4f46e5',
  },
  stepText: {
    flex: 1,
    fontSize: 15,
    color: '#374151',
    lineHeight: 21,
  },
});
