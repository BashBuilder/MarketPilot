"use client";

import { ImageOff } from "lucide-react";
import { useState } from "react";

export interface AssetPreviewProps {
  src: string | null;
  alt: string;
}

export function AssetPreview({ src, alt }: AssetPreviewProps) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <div
        role="img"
        aria-label={`${alt} (image unavailable)`}
        className="flex aspect-[4/3] w-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted text-muted-foreground"
      >
        <ImageOff aria-hidden="true" className="size-6" />
        <p className="px-4 text-center text-small">Image could not be loaded</p>
      </div>
    );
  }

  return (
    // Assets are backend URIs, so Next image optimisation is intentionally bypassed.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      onError={() => setFailed(true)}
      className="aspect-[4/3] w-full rounded-lg border border-border bg-muted object-cover"
    />
  );
}
