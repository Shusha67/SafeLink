import { CONFIG } from '../utils/config';

export type SafetyLevel = 'safe' | 'suspicious' | 'dangerous';

export interface ScanResult {
  url: string;
  score: number;
  level: SafetyLevel;
  report: string;
}

function classifyScore(score: number): SafetyLevel {
  if (score >= 85) return 'safe';
  if (score >= 50) return 'suspicious';
  return 'dangerous';
}

export async function scanUrl(url: string): Promise<ScanResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);

  try {
    const response = await fetch(`${CONFIG.API_BASE_URL}/api/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: url }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    const result = data.results[0];

    // Extract score from the report text (format: "Score: NN/100")
    const scoreMatch = result.report.match(/Score:\s*(\d+)\/100/);
    const score = scoreMatch ? parseInt(scoreMatch[1], 10) : 0;

    return {
      url: result.url,
      score,
      level: classifyScore(score),
      report: result.report,
    };
  } finally {
    clearTimeout(timeout);
  }
}
