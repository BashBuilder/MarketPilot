import { CheckCircle2, XCircle } from "lucide-react";
import type { ComplianceReport as ComplianceReportData } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";

export interface ComplianceReportProps {
  compliance?: ComplianceReportData | null;
}

export function ComplianceReport({ compliance }: ComplianceReportProps) {
  return (
    <ReviewSection
      id="compliance"
      title="Compliance"
      caption="Every claim checked against policy. Failures include the reviewer's reason."
    >
      {!compliance || compliance.items.length === 0 ? (
        <EmptyState
          headingLevel={3}
          title="Compliance not produced"
          description="This version was captured before the Compliance agent finished."
        />
      ) : (
        <ul className="space-y-3">
          {compliance.items.map((item, index) => {
            const Icon = item.passed ? CheckCircle2 : XCircle;
            return (
              <li
                key={`${item.check}-${index}`}
                className={cn(
                  "flex items-start gap-3 rounded-lg border px-4 py-3",
                  item.passed
                    ? "border-emerald-600/30 bg-emerald-500/5"
                    : "border-destructive/40 bg-destructive/5",
                )}
              >
                <Icon
                  aria-hidden="true"
                  className={cn(
                    "mt-0.5 size-5 shrink-0",
                    item.passed
                      ? "text-emerald-700 dark:text-emerald-300"
                      : "text-destructive",
                  )}
                />
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-small font-medium text-foreground">{item.check}</p>
                    <span
                      className={cn(
                        "rounded-full border px-2 py-0.5 text-caption font-medium",
                        item.passed
                          ? "border-emerald-600/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200"
                          : "border-destructive/40 bg-destructive/10 text-destructive",
                      )}
                    >
                      {item.passed ? "Pass" : "Fail"}
                    </span>
                  </div>
                  <p className="mt-1 text-small text-muted-foreground">{item.reason}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </ReviewSection>
  );
}
