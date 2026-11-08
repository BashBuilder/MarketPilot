import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  applyTheme,
  getStoredTheme,
  isTheme,
  nextTheme,
  setThemePreference,
  subscribeToTheme,
  THEME_STORAGE_KEY,
} from "./theme";

describe("theme", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.className = "";
    delete document.documentElement.dataset.theme;
    document.documentElement.style.colorScheme = "";
  });

  it("cycles through light, dark and system", () => {
    expect(nextTheme("light")).toBe("dark");
    expect(nextTheme("dark")).toBe("system");
    expect(nextTheme("system")).toBe("light");
  });

  it("validates stored theme values", () => {
    expect(isTheme("dark")).toBe(true);
    expect(isTheme("sepia")).toBe(false);

    window.localStorage.setItem(THEME_STORAGE_KEY, "sepia");
    expect(getStoredTheme()).toBe("system");
  });

  it("persists and applies a theme", () => {
    setThemePreference("dark");

    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(document.documentElement).toHaveClass("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");

    applyTheme("light");

    expect(document.documentElement).not.toHaveClass("dark");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("notifies subscribers until they unsubscribe", () => {
    const listener = vi.fn();
    const unsubscribe = subscribeToTheme(listener);

    setThemePreference("dark");
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    setThemePreference("light");
    expect(listener).toHaveBeenCalledTimes(1);
  });
});
