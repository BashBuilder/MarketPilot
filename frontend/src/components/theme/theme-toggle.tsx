"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useSyncExternalStore } from "react";
import { Button } from "@/components/ui/button";
import {
  getServerTheme,
  getStoredTheme,
  nextTheme,
  setThemePreference,
  subscribeToTheme,
  THEME_LABELS,
} from "@/lib/theme";

const ICONS = {
  light: Sun,
  dark: Moon,
  system: Monitor,
} as const;

export function ThemeToggle() {
  const theme = useSyncExternalStore(
    subscribeToTheme,
    getStoredTheme,
    getServerTheme,
  );
  const Icon = ICONS[theme];
  const upcoming = nextTheme(theme);

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={() => setThemePreference(nextTheme(theme))}
      aria-label={`Theme: ${THEME_LABELS[theme]}. Switch to ${THEME_LABELS[upcoming]}.`}
      title={`Theme: ${THEME_LABELS[theme]}`}
    >
      <Icon aria-hidden="true" />
    </Button>
  );
}
