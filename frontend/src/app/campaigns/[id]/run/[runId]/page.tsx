import { LiveRunView } from "@/components/agents/LiveRunView";

export const instant = false;

interface RunPageProps {
  params: Promise<{ id: string; runId: string }>;
}

export default async function RunPage({ params }: RunPageProps) {
  const { id, runId } = await params;

  return <LiveRunView campaignId={id} runId={runId} />;
}
