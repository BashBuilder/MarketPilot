import { PageContainer } from "@/components/layout/page-container";
import { SkeletonBlock } from "@/components/states/skeleton-block";

export default function VersionReviewLoading() {
  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <SkeletonBlock label="Loading version review" lines={3} className="max-w-xl" />
        <div className="mt-8 space-y-6" aria-hidden="true">
          {Array.from({ length: 6 }, (_, index) => (
            <div
              key={index}
              className="rounded-xl border border-border bg-card px-5 py-6 sm:px-6"
            >
              <SkeletonBlock lines={index === 0 ? 5 : 3} />
            </div>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
