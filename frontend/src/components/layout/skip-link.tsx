export function SkipLink() {
  return (
    <a
      href="#main-content"
      className="sr-only rounded-md bg-brand px-4 py-2 text-small font-medium text-brand-foreground focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50"
    >
      Skip to content
    </a>
  );
}
