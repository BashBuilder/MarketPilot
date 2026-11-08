export type ThemeName = "light" | "dark";

export interface ColorToken {
  name: string;
  variable: string;
  value: string;
}

export const COLOR_TOKEN_NAMES = [
  "background",
  "foreground",
  "card",
  "card-foreground",
  "popover",
  "popover-foreground",
  "primary",
  "primary-foreground",
  "secondary",
  "secondary-foreground",
  "muted",
  "muted-foreground",
  "accent",
  "accent-foreground",
  "destructive",
  "destructive-foreground",
  "border",
  "input",
  "ring",
  "brand",
  "brand-foreground",
  "brand-muted",
] as const;

export type ColorTokenName = (typeof COLOR_TOKEN_NAMES)[number];

export const LIGHT_COLORS: Record<ColorTokenName, string> = {
  background: "oklch(0.985 0.006 85)",
  foreground: "oklch(0.235 0.014 70)",
  card: "oklch(0.995 0.004 85)",
  "card-foreground": "oklch(0.235 0.014 70)",
  popover: "oklch(0.995 0.004 85)",
  "popover-foreground": "oklch(0.235 0.014 70)",
  primary: "oklch(0.455 0.088 188)",
  "primary-foreground": "oklch(0.99 0.004 85)",
  secondary: "oklch(0.95 0.009 80)",
  "secondary-foreground": "oklch(0.29 0.014 70)",
  muted: "oklch(0.955 0.008 80)",
  "muted-foreground": "oklch(0.46 0.014 70)",
  accent: "oklch(0.945 0.025 185)",
  "accent-foreground": "oklch(0.3 0.035 188)",
  destructive: "oklch(0.505 0.17 27)",
  "destructive-foreground": "oklch(0.99 0.004 85)",
  border: "oklch(0.895 0.009 80)",
  input: "oklch(0.895 0.009 80)",
  ring: "oklch(0.52 0.09 188)",
  brand: "oklch(0.455 0.088 188)",
  "brand-foreground": "oklch(0.99 0.004 85)",
  "brand-muted": "oklch(0.945 0.025 185)",
};

export const DARK_COLORS: Record<ColorTokenName, string> = {
  background: "oklch(0.17 0.012 70)",
  foreground: "oklch(0.955 0.008 85)",
  card: "oklch(0.215 0.012 70)",
  "card-foreground": "oklch(0.955 0.008 85)",
  popover: "oklch(0.215 0.012 70)",
  "popover-foreground": "oklch(0.955 0.008 85)",
  primary: "oklch(0.72 0.085 188)",
  "primary-foreground": "oklch(0.18 0.018 188)",
  secondary: "oklch(0.27 0.012 70)",
  "secondary-foreground": "oklch(0.955 0.008 85)",
  muted: "oklch(0.255 0.01 70)",
  "muted-foreground": "oklch(0.755 0.012 80)",
  accent: "oklch(0.29 0.035 188)",
  "accent-foreground": "oklch(0.92 0.025 188)",
  destructive: "oklch(0.72 0.15 25)",
  "destructive-foreground": "oklch(0.18 0.02 25)",
  border: "oklch(0.33 0.012 70)",
  input: "oklch(0.33 0.012 70)",
  ring: "oklch(0.72 0.085 188)",
  brand: "oklch(0.72 0.085 188)",
  "brand-foreground": "oklch(0.18 0.018 188)",
  "brand-muted": "oklch(0.29 0.035 188)",
};

export const THEME_COLORS: Record<ThemeName, Record<ColorTokenName, string>> = {
  light: LIGHT_COLORS,
  dark: DARK_COLORS,
};

export function colorTokens(theme: ThemeName): ColorToken[] {
  const colors = THEME_COLORS[theme];
  return COLOR_TOKEN_NAMES.map((name) => ({
    name,
    variable: `--${name}`,
    value: colors[name],
  }));
}
