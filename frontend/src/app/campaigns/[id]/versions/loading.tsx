import { PageContainer } from "@/components/layout/page-container";
import { SkeletonBlock } from "@/components/states/skeleton-block";

export default function VersionsLoading() {
  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <SkeletonBlock label="Loading version history" lines={3} className="max-w-xl" />
        <div aria-hidden="true" className="mt-8 space-y-3">
          {Array.from({ length: 3 }, (_, index) => (
            <div
              key={index}
              className="rounded-xl border border-border bg-card px-5 py-4"
            >
              <SkeletonBlock lines={2} />
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
