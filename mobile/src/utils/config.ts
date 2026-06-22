export const CONFIG = {
  API_BASE_URL: __DEV__
    ? 'http://10.0.2.2:8000'   // Android emulator → host machine
    : 'https://api.safelink.example.com',

  CLIPBOARD_POLL_INTERVAL_MS: 1500,

  NOTIFICATION_CHANNEL_ID: 'safelink-alerts',
  NOTIFICATION_CHANNEL_NAME: 'SafeLink Alerts',
} as const;

declare const __DEV__: boolean;
