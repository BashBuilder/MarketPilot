import type { Agent, StreamActor } from "@/lib/schemas";
import type { AgentStatus } from "@/lib/sse/run-state";

export interface AgentMeta {
  name: string;
  description: string;
}

export const AGENT_META: Record<Agent, AgentMeta> = {
  brief: {
    name: "Brief",
    description: "Turns the campaign idea into a structured brief.",
  },
  research: {
    name: "Research",
    description: "Finds audience segments, pain points and messaging angles.",
  },
  copywriter: {
    name: "Copywriter",
    description: "Writes channel-ready headlines, descriptions and CTAs.",
  },
  creative_director: {
    name: "Creative Director",
    description: "Sets the visual style and image prompts.",
  },
  designer: {
    name: "Designer",
    description: "Generates and stores the campaign assets.",
  },
  compliance: {
    name: "Compliance",
    description: "Checks every claim against policy.",
  },
  reviewer: {
    name: "Reviewer",
    description: "Scores the package and routes weak work back.",
  },
  supervisor: {
    name: "Supervisor",
    description: "Routes the run between agents and the human gate.",
  },
};

export const STATUS_LABELS: Record<AgentStatus, string> = {
  waiting: "Waiting",
  running: "Running",
  retrying: "Retrying",
  failed: "Failed",
  done: "Done",
};

export function actorName(actor: StreamActor): string {
  return actor === "human" ? "Human review" : AGENT_META[actor].name;
}
