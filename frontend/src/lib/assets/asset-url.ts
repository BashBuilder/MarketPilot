const HTTP_PROTOCOLS = new Set(["http:", "https:"]);

/**
 * Hosted assets are absolute `https://` URLs; everything else is a backend
 * file name served through the same-origin `/api/assets` proxy. Unsafe
 * schemes (for example `javascript:` or `data:`) are rejected.
 */
export function resolveAssetUrl(uri: string): string | null {
  const trimmed = uri.trim();
  if (trimmed.length === 0) return null;

  try {
    const absolute = new URL(trimmed);
    return HTTP_PROTOCOLS.has(absolute.protocol) ? absolute.toString() : null;
  } catch {
    // Not an absolute URL: fall through to the local proxy.
  }

  const relative = trimmed.replace(/^\.?\/+/, "");
  if (relative.length === 0) return null;

  return `/api/assets/${relative
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/")}`;
}
