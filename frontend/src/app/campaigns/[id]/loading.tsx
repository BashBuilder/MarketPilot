import { PageContainer } from "@/components/layout/page-container";
import { SkeletonBlock } from "@/components/states/skeleton-block";

export default function CampaignOverviewLoading() {
  return (
    <PageContainer className="py-10 sm:py-14">
      <div className="mx-auto max-w-4xl">
        <SkeletonBlock label="Loading campaign" lines={3} className="max-w-xl" />
        <div
          aria-hidden="true"
          className="mt-8 rounded-xl border border-border bg-card px-6 py-5"
        >
          <SkeletonBlock lines={4} />
        </div>
      </div>
    </PageContainer>
  );
}
