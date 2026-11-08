/**
 * Single source of truth for the design tokens rendered by `/style` and for
 * the WCAG contrast tests. Keep these values in sync with `globals.css`.
 */

import type { ColorTokenName, ThemeName } from "./color-tokens";

export * from "./color-tokens";

export interface ScaleToken {
  name: string;
  variable: string;
  value: string;
  description?: string;
}

const CHART_COLORS: Record<ThemeName, string[]> = {
  light: [
    "oklch(0.455 0.088 188)",
    "oklch(0.575 0.07 188)",
    "oklch(0.68 0.05 188)",
    "oklch(0.78 0.03 188)",
    "oklch(0.88 0.015 188)",
  ],
  dark: [
    "oklch(0.72 0.085 188)",
    "oklch(0.62 0.07 188)",
    "oklch(0.52 0.055 188)",
    "oklch(0.42 0.04 188)",
    "oklch(0.33 0.025 188)",
  ],
};

export function chartTokens(theme: ThemeName): ScaleToken[] {
  return CHART_COLORS[theme].map((value, index) => ({
    name: `chart-${index + 1}`,
    variable: `--chart-${index + 1}`,
    value,
  }));
}

export const TYPE_SCALE: ScaleToken[] = [
  { name: "display", variable: "--text-display", value: "3rem" },
  { name: "title", variable: "--text-title", value: "2rem" },
  { name: "heading", variable: "--text-heading", value: "1.5rem" },
  { name: "subheading", variable: "--text-subheading", value: "1.125rem" },
  { name: "body", variable: "--text-body", value: "1rem" },
  { name: "small", variable: "--text-small", value: "0.875rem" },
  { name: "caption", variable: "--text-caption", value: "0.75rem" },
];

export const SPACING_SCALE: ScaleToken[] = [
  { name: "3xs", variable: "--spacing-3xs", value: "0.25rem" },
  { name: "2xs", variable: "--spacing-2xs", value: "0.5rem" },
  { name: "xs", variable: "--spacing-xs", value: "0.75rem" },
  { name: "sm", variable: "--spacing-sm", value: "1rem" },
  { name: "md", variable: "--spacing-md", value: "1.5rem" },
  { name: "lg", variable: "--spacing-lg", value: "2rem" },
  { name: "xl", variable: "--spacing-xl", value: "3rem" },
  { name: "2xl", variable: "--spacing-2xl", value: "4rem" },
  { name: "3xl", variable: "--spacing-3xl", value: "6rem" },
];

export const RADIUS_SCALE: ScaleToken[] = [
  { name: "sm", variable: "--radius-sm", value: "calc(var(--radius) * 0.6)" },
  { name: "md", variable: "--radius-md", value: "calc(var(--radius) * 0.8)" },
  { name: "lg", variable: "--radius-lg", value: "var(--radius)" },
  { name: "xl", variable: "--radius-xl", value: "calc(var(--radius) * 1.4)" },
];

export interface ContrastPair {
  label: string;
  foreground: ColorTokenName;
  background: ColorTokenName;
  minimum: number;
}

export const CONTRAST_PAIRS: ContrastPair[] = [
  { label: "Body text", foreground: "foreground", background: "background", minimum: 4.5 },
  { label: "Body text on card", foreground: "foreground", background: "card", minimum: 4.5 },
  { label: "Muted text", foreground: "muted-foreground", background: "background", minimum: 4.5 },
  { label: "Muted text on muted", foreground: "muted-foreground", background: "muted", minimum: 4.5 },
  { label: "Popover text", foreground: "popover-foreground", background: "popover", minimum: 4.5 },
  { label: "Primary button", foreground: "primary-foreground", background: "primary", minimum: 4.5 },
  { label: "Secondary button", foreground: "secondary-foreground", background: "secondary", minimum: 4.5 },
  { label: "Accent text", foreground: "accent-foreground", background: "accent", minimum: 4.5 },
  { label: "Brand text", foreground: "brand-foreground", background: "brand", minimum: 4.5 },
  { label: "Destructive text", foreground: "destructive", background: "background", minimum: 4.5 },
  { label: "Destructive button", foreground: "destructive-foreground", background: "destructive", minimum: 4.5 },
];
