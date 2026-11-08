import { THEME_INIT_SCRIPT } from "@/lib/theme";

/**
 * Inline pre-paint script. The string is a local constant, never user content,
 * so `dangerouslySetInnerHTML` is the correct escape hatch here.
 */
export function ThemeScript() {
  return (
    <script
      dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }}
      suppressHydrationWarning
    />
  );
}
