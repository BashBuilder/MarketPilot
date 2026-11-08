import { API_BASE_URL } from "@/lib/api";
import { SseEventSchema, isTerminalEvent, type SseEvent, type SseEventType } from "@/lib/schemas";
import type { ConnectionStatus, MalformedEvent } from "./run-state";

export const STALL_TIMEOUT_MS = 75_000;

const EVENT_TYPES: readonly SseEventType[] = [
  "agent_started",
  "agent_handoff",
  "tool_called",
  "validation_failed",
  "retrying",
  "awaiting_approval",
  "completed",
  "error",
];

export interface StreamCallbacks {
  onConnection: (connection: ConnectionStatus) => void;
  onEvent: (event: SseEvent, lastEventId: string | null) => void;
  onMalformed: (malformed: MalformedEvent, lastEventId: string | null) => void;
}

/** Opens the run stream and returns its cleanup function. */
export function openRunStream(runId: string, callbacks: StreamCallbacks): () => void {
  if (typeof EventSource === "undefined") {
    callbacks.onConnection("closed");
    return () => undefined;
  }

  const source = new EventSource(
    `${API_BASE_URL}/runs/${encodeURIComponent(runId)}/stream`,
  );
  let active = true;
  let terminal = false;
  let stallTimer: ReturnType<typeof setTimeout> | undefined;

  const clearStall = () => {
    if (stallTimer !== undefined) clearTimeout(stallTimer);
    stallTimer = undefined;
  };

  const armStall = () => {
    clearStall();
    stallTimer = setTimeout(() => {
      if (active && !terminal) callbacks.onConnection("stalled");
    }, STALL_TIMEOUT_MS);
  };

  const closeTerminal = () => {
    terminal = true;
    clearStall();
    source.close();
    callbacks.onConnection("closed");
  };

  const handleEvent = (type: SseEventType) => (message: MessageEvent<string>) => {
    if (!active || terminal) return;
    armStall();
    callbacks.onConnection("open");

    let payload: unknown;
    try {
      payload = JSON.parse(message.data) as unknown;
    } catch {
      callbacks.onMalformed(
        {
          id: message.lastEventId || null,
          event: type,
          message: "Event data is not valid JSON.",
        },
        message.lastEventId || null,
      );
      return;
    }

    const parsed = SseEventSchema.safeParse({
      id: message.lastEventId,
      event: type,
      data: payload,
    });
    if (!parsed.success) {
      callbacks.onMalformed(
        {
          id: message.lastEventId || null,
          event: type,
          message: parsed.error.issues.map((issue) => issue.message).join("; "),
        },
        message.lastEventId || null,
      );
      return;
    }

    callbacks.onEvent(parsed.data, message.lastEventId || null);
    if (isTerminalEvent(parsed.data)) closeTerminal();
  };

  const onOpen = () => {
    if (!active || terminal) return;
    callbacks.onConnection("open");
    armStall();
  };

  const onError = () => {
    if (!active || terminal) return;
    // Keep the EventSource open after an unexpected drop. The browser
    // reconnects natively and sends Last-Event-ID from the last frame.
    if (source.readyState === 2) {
      clearStall();
      callbacks.onConnection("closed");
    } else {
      callbacks.onConnection("reconnecting");
    }
  };

  const eventListeners = EVENT_TYPES.map((type) => {
    const listener = handleEvent(type);
    source.addEventListener(type, listener as EventListener);
    return [type, listener] as const;
  });
  source.addEventListener("open", onOpen);
  source.addEventListener("error", onError);

  return () => {
    active = false;
    clearStall();
    for (const [type, listener] of eventListeners) {
      source.removeEventListener(type, listener as EventListener);
    }
    source.removeEventListener("open", onOpen);
    source.removeEventListener("error", onError);
    source.close();
  };
}
