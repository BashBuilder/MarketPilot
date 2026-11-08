export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export const THEME_STORAGE_KEY = "marketpilot-theme";

export const THEME_LABELS: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
};

const THEME_ORDER: Theme[] = ["light", "dark", "system"];

export function isTheme(value: unknown): value is Theme {
  return value === "light" || value === "dark" || value === "system";
}

function mediaQuery(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return null;
  }
  return window.matchMedia("(prefers-color-scheme: dark)");
}

export function getSystemTheme(): ResolvedTheme {
  return mediaQuery()?.matches ? "dark" : "light";
}

export function resolveTheme(theme: Theme): ResolvedTheme {
  return theme === "system" ? getSystemTheme() : theme;
}

export function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "system";
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isTheme(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

export function setStoredTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Private browsing can deny storage; the in-memory theme still applies.
  }
}

export function nextTheme(theme: Theme): Theme {
  return THEME_ORDER[(THEME_ORDER.indexOf(theme) + 1) % THEME_ORDER.length];
}

type ThemeListener = () => void;
const listeners = new Set<ThemeListener>();

function notifyThemeListeners(): void {
  for (const listener of listeners) listener();
}

export function applyTheme(
  theme: Theme,
  root: HTMLElement = document.documentElement,
): ResolvedTheme {
  const resolved = resolveTheme(theme);
  root.classList.toggle("dark", resolved === "dark");
  root.dataset.theme = resolved;
  root.style.colorScheme = resolved;
  return resolved;
}

/** Persists the choice, applies it and tells every subscriber to re-read. */
export function setThemePreference(theme: Theme): void {
  setStoredTheme(theme);
  applyTheme(theme);
  notifyThemeListeners();
}

/** Runs before paint so the first frame already has the right palette. */
export const THEME_INIT_SCRIPT = `(function(){try{var key="marketpilot-theme";var stored=window.localStorage.getItem(key);var theme=stored==="light"||stored==="dark"||stored==="system"?stored:"system";var dark=theme==="dark"||(theme==="system"&&window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches);var root=document.documentElement;root.classList.toggle("dark",dark);root.dataset.theme=dark?"dark":"light";root.style.colorScheme=dark?"dark":"light";}catch(error){}})();`;

export function subscribeToTheme(listener: ThemeListener): () => void {
  if (typeof window === "undefined") return () => undefined;

  listeners.add(listener);

  const onStorage = (event: StorageEvent) => {
    if (event.key !== THEME_STORAGE_KEY) return;
    applyTheme(getStoredTheme());
    notifyThemeListeners();
  };

  const query = mediaQuery();
  const onSystemChange = () => {
    if (getStoredTheme() !== "system") return;
    applyTheme("system");
    notifyThemeListeners();
  };

  window.addEventListener("storage", onStorage);
  query?.addEventListener("change", onSystemChange);

  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
    query?.removeEventListener("change", onSystemChange);
  };
}

export function getServerTheme(): Theme {
  return "system";
}
