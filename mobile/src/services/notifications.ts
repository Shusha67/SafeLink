import notifee, {
  AndroidImportance,
  AndroidColor,
  EventType,
  Event,
} from '@notifee/react-native';
import { CONFIG } from '../utils/config';
import { scanUrl, SafetyLevel } from './api';

const PROMPT_NOTIFICATION_ID = 'safelink-prompt';
const RESULT_NOTIFICATION_ID = 'safelink-result';

const ACTION_CHECK = 'check';
const ACTION_DISMISS = 'dismiss';

const LEVEL_DISPLAY: Record<SafetyLevel, {
  title: string;
  emoji: string;
  color: string;
  androidColor: string;
}> = {
  safe: {
    title: 'Safe Link',
    emoji: '🟢',
    color: '#22c55e',
    androidColor: AndroidColor.GREEN,
  },
  suspicious: {
    title: 'Suspicious Link',
    emoji: '🟡',
    color: '#eab308',
    androidColor: AndroidColor.YELLOW,
  },
  dangerous: {
    title: 'Unsafe Link',
    emoji: '🔴',
    color: '#ef4444',
    androidColor: AndroidColor.RED,
  },
};

export async function setupNotificationChannel(): Promise<void> {
  await notifee.createChannel({
    id: CONFIG.NOTIFICATION_CHANNEL_ID,
    name: CONFIG.NOTIFICATION_CHANNEL_NAME,
    importance: AndroidImportance.HIGH,
    vibration: true,
  });
}

export async function showClipboardPrompt(url: string): Promise<void> {
  const truncated = url.length > 50 ? url.substring(0, 47) + '...' : url;

  await notifee.displayNotification({
    id: PROMPT_NOTIFICATION_ID,
    title: '🔗 You copied a link',
    body: `Do you want SafeLink to check if it's safe?\n${truncated}`,
    data: { url },
    android: {
      channelId: CONFIG.NOTIFICATION_CHANNEL_ID,
      importance: AndroidImportance.HIGH,
      smallIcon: 'ic_notification',
      color: '#4f46e5',
      pressAction: { id: ACTION_CHECK },
      actions: [
        {
          title: '✅ Yes, Check',
          pressAction: { id: ACTION_CHECK },
        },
        {
          title: 'Dismiss',
          pressAction: { id: ACTION_DISMISS },
        },
      ],
      autoCancel: true,
    },
    ios: {
      categoryId: 'safelink-check',
      interruptionLevel: 'timeSensitive',
    },
  });
}

async function showScanningNotification(): Promise<void> {
  await notifee.displayNotification({
    id: RESULT_NOTIFICATION_ID,
    title: '🔍 Scanning...',
    body: 'Checking link safety now',
    android: {
      channelId: CONFIG.NOTIFICATION_CHANNEL_ID,
      importance: AndroidImportance.LOW,
      smallIcon: 'ic_notification',
      color: '#4f46e5',
      ongoing: true,
      autoCancel: false,
    },
  });
}

async function showResultNotification(
  url: string,
  level: SafetyLevel,
  score: number,
): Promise<void> {
  const display = LEVEL_DISPLAY[level];
  const truncated = url.length > 40 ? url.substring(0, 37) + '...' : url;

  await notifee.displayNotification({
    id: RESULT_NOTIFICATION_ID,
    title: `${display.emoji} ${display.title}`,
    body: `Score: ${score}/100 — ${truncated}`,
    android: {
      channelId: CONFIG.NOTIFICATION_CHANNEL_ID,
      importance: AndroidImportance.HIGH,
      smallIcon: 'ic_notification',
      color: display.androidColor,
      autoCancel: true,
    },
    ios: {
      interruptionLevel: 'timeSensitive',
    },
  });
}

async function showErrorNotification(): Promise<void> {
  await notifee.displayNotification({
    id: RESULT_NOTIFICATION_ID,
    title: '⚠️ Check Failed',
    body: 'Could not reach SafeLink server. Try again later.',
    android: {
      channelId: CONFIG.NOTIFICATION_CHANNEL_ID,
      importance: AndroidImportance.HIGH,
      smallIcon: 'ic_notification',
      color: AndroidColor.RED,
      autoCancel: true,
    },
  });
}

export async function handleNotificationAction(event: Event): Promise<void> {
  const { type, detail } = event;

  if (type !== EventType.ACTION_PRESS && type !== EventType.PRESS) return;

  const actionId = detail.pressAction?.id;
  const url = detail.notification?.data?.url as string | undefined;

  if (actionId === ACTION_DISMISS) {
    await notifee.cancelNotification(PROMPT_NOTIFICATION_ID);
    return;
  }

  if ((actionId === ACTION_CHECK || type === EventType.PRESS) && url) {
    await notifee.cancelNotification(PROMPT_NOTIFICATION_ID);
    await showScanningNotification();

    try {
      const result = await scanUrl(url);
      await showResultNotification(url, result.level, result.score);
    } catch {
      await showErrorNotification();
    }
  }
}
