import type { AssetSet, CreativeDirection } from "@/lib/schemas";
import { resolveAssetUrl } from "@/lib/assets/asset-url";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";
import { AssetPreview } from "./AssetPreview";

export interface AssetGridProps {
  assets?: AssetSet | null;
  direction?: CreativeDirection | null;
}

export function AssetGrid({ assets, direction }: AssetGridProps) {
  const items = assets?.assets ?? [];

  return (
    <ReviewSection
      id="assets"
      title="Images"
      caption="Generated creative, with the prompt and seed behind each image."
    >
      {items.length === 0 ? (
        <EmptyState
          headingLevel={3}
          title="No images produced"
          description="This version has no generated assets yet."
        />
      ) : (
        <ul className="grid gap-5 sm:grid-cols-2">
          {items.map((asset, index) => {
            const alt = direction?.image_prompts[index] ?? asset.prompt;
            return (
              <li
                key={`${asset.uri}-${index}`}
                className="flex flex-col rounded-lg border border-border bg-background p-3"
              >
                <AssetPreview src={resolveAssetUrl(asset.uri)} alt={alt} />
                <details className="mt-3 text-small">
                  <summary className="cursor-pointer font-medium text-foreground">
                    Details
                  </summary>
                  <dl className="mt-2 space-y-1">
                    <div className="flex gap-2">
                      <dt className="shrink-0 text-muted-foreground">Prompt</dt>
                      <dd className="text-foreground">{asset.prompt}</dd>
                    </div>
                    <div className="flex gap-2">
                      <dt className="shrink-0 text-muted-foreground">Model</dt>
                      <dd className="text-foreground">{asset.model}</dd>
                    </div>
                    <div className="flex gap-2">
                      <dt className="shrink-0 text-muted-foreground">Seed</dt>
                      <dd className="font-mono text-foreground">{String(asset.seed)}</dd>
                    </div>
                  </dl>
                </details>
              </li>
            );
          })}
        </ul>
      )}
    </ReviewSection>
  );
}
