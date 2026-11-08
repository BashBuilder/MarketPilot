"use client";

import { useEffect, useState } from "react";
import { applySseEvent, recordMalformedEvent } from "./reducer";
import { createInitialRunState, type ConnectionStatus, type RunState } from "./run-state";
import { openRunStream } from "./stream-source";

export { STALL_TIMEOUT_MS } from "./stream-source";

export interface UseRunStreamResult {
  state: RunState;
  connection: ConnectionStatus;
  lastEventId: string | null;
}

interface StreamSnapshot {
  runId: string;
  state: RunState;
  connection: ConnectionStatus;
  lastEventId: string | null;
}

function createSnapshot(runId: string): StreamSnapshot {
  return {
    runId,
    state: createInitialRunState(runId),
    connection: "connecting",
    lastEventId: null,
  };
}

export function useRunStream(runId: string): UseRunStreamResult {
  const [snapshot, setSnapshot] = useState<StreamSnapshot>(() => createSnapshot(runId));
  const current = snapshot.runId === runId ? snapshot : createSnapshot(runId);

  useEffect(() => {
    const update = (patch: (base: StreamSnapshot) => StreamSnapshot) => {
      setSnapshot((previous) => patch(previous.runId === runId ? previous : createSnapshot(runId)));
    };

    return openRunStream(runId, {
      onConnection: (connection) => update((base) => ({ ...base, connection })),
      onEvent: (event, lastEventId) =>
        update((base) => ({
          ...base,
          lastEventId: lastEventId ?? base.lastEventId,
          state: applySseEvent(base.state, event),
        })),
      onMalformed: (malformed, lastEventId) =>
        update((base) => ({
          ...base,
          lastEventId: lastEventId ?? base.lastEventId,
          state: recordMalformedEvent(base.state, malformed),
        })),
    });
  }, [runId]);

  return {
    state: current.state,
    connection: current.connection,
    lastEventId: current.lastEventId,
  };
}
