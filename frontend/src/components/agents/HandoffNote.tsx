import { ArrowRight } from "lucide-react";
import type { Handoff } from "@/lib/sse/run-state";
import { formatTime } from "./agent-format";
import { actorName } from "./agent-meta";

export interface HandoffNoteProps {
  handoff: Handoff;
}

export function HandoffNote({ handoff }: HandoffNoteProps) {
  return (
    <li className="flex flex-wrap items-center gap-2 text-small">
      <span className="font-medium text-foreground">{actorName(handoff.from)}</span>
      <ArrowRight aria-hidden="true" className="size-3.5 text-muted-foreground" />
      <span className="text-muted-foreground">handed off to</span>
      <span className="font-medium text-foreground">{actorName(handoff.to)}</span>
      <time
        dateTime={handoff.timestamp}
        className="ml-auto text-caption text-muted-foreground"
      >
        {formatTime(handoff.timestamp)}
      </time>
    </li>
  );
}
