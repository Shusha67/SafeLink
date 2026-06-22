import React, { useEffect } from 'react';
import notifee from '@notifee/react-native';
import {
  setupNotificationChannel,
  handleNotificationAction,
} from './services/notifications';
import StatusScreen from './components/StatusScreen';

// Handle notification actions when app is in foreground
notifee.onForegroundEvent(handleNotificationAction);

// Handle notification actions when app is in background/quit
notifee.onBackgroundEvent(handleNotificationAction);

export default function App(): React.JSX.Element {
  useEffect(() => {
    setupNotificationChannel();
  }, []);

  return <StatusScreen />;
}
