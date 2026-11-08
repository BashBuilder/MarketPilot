/**
 * WCAG 2.x contrast helpers for the OKLCH tokens used in `globals.css`.
 * OKLCH is converted to linear sRGB first, which is exactly what the relative
 * luminance formula expects.
 */

interface LinearRgb {
  r: number;
  g: number;
  b: number;
}

const OKLCH_PATTERN =
  /^oklch\(\s*([+-]?[\d.]+)(%?)\s+([+-]?[\d.]+)\s+([+-]?[\d.]+)(?:deg)?(?:\s*\/\s*[^)]+)?\s*\)$/;

const clamp = (value: number): number => Math.min(1, Math.max(0, value));

export function oklchToLinearRgb(value: string): LinearRgb {
  const match = OKLCH_PATTERN.exec(value.trim());
  if (!match) {
    throw new Error(`Unsupported colour value: ${value}`);
  }

  const lightness = Number(match[1]) / (match[2] === "%" ? 100 : 1);
  const chroma = Number(match[3]);
  const hue = (Number(match[4]) * Math.PI) / 180;
  const a = chroma * Math.cos(hue);
  const b = chroma * Math.sin(hue);

  const lPrime = lightness + 0.3963377774 * a + 0.2158037573 * b;
  const mPrime = lightness - 0.1055613458 * a - 0.0638541728 * b;
  const sPrime = lightness - 0.0894841775 * a - 1.291485548 * b;

  const l = lPrime ** 3;
  const m = mPrime ** 3;
  const s = sPrime ** 3;

  return {
    r: clamp(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    g: clamp(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    b: clamp(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  };
}

export function relativeLuminance(value: string): number {
  const { r, g, b } = oklchToLinearRgb(value);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(foreground: string, background: string): number {
  const first = relativeLuminance(foreground);
  const second = relativeLuminance(background);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

export function tokenContrast(
  foreground: string,
  background: string,
): number {
  return contrastRatio(foreground, background);
}

export function formatRatio(ratio: number): string {
  return `${ratio.toFixed(2)}:1`;
}
