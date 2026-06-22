const URL_PATTERN = /https?:\/\/[^\s<>"'`,;)\]}>]+/i;

export function extractUrl(text: string): string | null {
  const match = text.match(URL_PATTERN);
  return match ? match[0] : null;
}
