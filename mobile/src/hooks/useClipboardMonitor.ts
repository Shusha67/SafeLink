import { useEffect, useRef, useCallback } from 'react';
import Clipboard from '@react-native-clipboard/clipboard';
import { AppState, AppStateStatus } from 'react-native';
import { extractUrl } from '../utils/urlDetector';
import { showClipboardPrompt } from '../services/notifications';
import { CONFIG } from '../utils/config';

export function useClipboardMonitor(): void {
  const lastSeenUrl = useRef<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkClipboard = useCallback(async () => {
    try {
      const hasString = await Clipboard.hasString();
      if (!hasString) return;

      const content = await Clipboard.getString();
      const url = extractUrl(content);

      if (url && url !== lastSeenUrl.current) {
        lastSeenUrl.current = url;
        await showClipboardPrompt(url);
      }
    } catch {
      // Clipboard access can fail silently on some OS versions
    }
  }, []);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(checkClipboard, CONFIG.CLIPBOARD_POLL_INTERVAL_MS);
  }, [checkClipboard]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    startPolling();
    // Run an immediate check when the app comes to foreground
    checkClipboard();

    const handleAppState = (state: AppStateStatus) => {
      if (state === 'active') {
        checkClipboard();
        startPolling();
      } else {
        stopPolling();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppState);

    return () => {
      stopPolling();
      subscription.remove();
    };
  }, [checkClipboard, startPolling, stopPolling]);
}
