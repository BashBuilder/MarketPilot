"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { SCORE_DIMENSIONS, type CreativeScore } from "@/lib/schemas";
import { EmptyState } from "@/components/states/empty-state";
import { ReviewSection } from "@/components/layout/review-section";

export interface ScoreBreakdownProps {
  score?: CreativeScore | null;
}

const DIMENSION_LABELS: Record<(typeof SCORE_DIMENSIONS)[number], string> = {
  brief_alignment: "Brief alignment",
  audience_fit: "Audience fit",
  copy_quality: "Copy quality",
  visual_quality: "Visual quality",
  compliance_risk: "Compliance risk",
};

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  const data = score
    ? SCORE_DIMENSIONS.map((key) => ({
        key,
        label: DIMENSION_LABELS[key],
        value: score[key].score,
        justification: score[key].justification,
      }))
    : [];

  const summary = data
    .map((item) => `${item.label}: ${item.value} out of 10`)
    .join(". ");

  return (
    <ReviewSection
      id="score"
      title="Creative score"
      caption="Each dimension is scored out of 10 and weighted equally (20%)."
    >
      {!score ? (
        <EmptyState
          headingLevel={3}
          title="Score not produced"
          description="The Reviewer has not scored this version yet."
        />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-baseline gap-2">
            <p className="text-display text-foreground">{Math.round(score.total)}</p>
            <p className="text-small text-muted-foreground">/ 100 weighted total</p>
          </div>

          <figure
            role="img"
            aria-label={`Creative score by dimension. ${summary}. Weighted total ${Math.round(
              score.total,
            )} out of 100.`}
          >
            <div aria-hidden="true" className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data}
                  layout="vertical"
                  margin={{ top: 4, right: 32, bottom: 4, left: 8 }}
                >
                  <CartesianGrid horizontal={false} stroke="var(--border)" />
                  <XAxis
                    type="number"
                    domain={[0, 10]}
                    ticks={[0, 5, 10]}
                    tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="label"
                    width={128}
                    tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Bar
                    dataKey="value"
                    fill="var(--chart-1)"
                    radius={[0, 4, 4, 0]}
                    isAnimationActive={false}
                  >
                    <LabelList
                      dataKey="value"
                      position="right"
                      fill="var(--foreground)"
                      fontSize={12}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <figcaption className="sr-only">{summary}</figcaption>
          </figure>

          <dl className="space-y-4">
            {data.map((item) => (
              <div key={item.key}>
                <dt className="flex flex-wrap items-baseline justify-between gap-2 text-small font-medium text-foreground">
                  <span>{item.label}</span>
                  <span className="text-muted-foreground">{item.value} / 10</span>
                </dt>
                <dd className="mt-1 text-small text-muted-foreground">
                  {item.justification}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </ReviewSection>
  );
}
