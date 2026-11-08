import type { SseEventType, StreamActor } from "@/lib/schemas";

type Listener = (event: Event) => void;

export const TEST_RUN_ID = "11111111-1111-4111-8111-111111111111";

export class FakeEventSource {
  static instances: FakeEventSource[] = [];
  readonly url: string;
  readyState = 0;
  closed = false;
  private listeners = new Map<string, Set<Listener>>();

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: Listener): void {
    const set = this.listeners.get(type) ?? new Set<Listener>();
    set.add(listener);
    this.listeners.set(type, set);
  }

  removeEventListener(type: string, listener: Listener): void {
    this.listeners.get(type)?.delete(listener);
  }

  close(): void {
    this.closed = true;
    this.readyState = 2;
  }

  open(): void {
    this.readyState = 1;
    this.dispatch("open", new Event("open"));
  }

  fail(): void {
    this.readyState = 0;
    this.dispatch("error", new Event("error"));
  }

  emit(type: SseEventType, data: unknown, id: string): void {
    this.dispatch(type, {
      type,
      data: JSON.stringify(data),
      lastEventId: id,
    } as MessageEvent<string>);
  }

  emitRaw(type: SseEventType, data: string, id: string): void {
    this.dispatch(type, { type, data, lastEventId: id } as MessageEvent<string>);
  }

  private dispatch(type: string, event: Event): void {
    for (const listener of this.listeners.get(type) ?? []) listener(event);
  }
}

export function sseData(agent: StreamActor, extra: Record<string, unknown> = {}) {
  return { run_id: TEST_RUN_ID, timestamp: "2026-01-01T10:00:00Z", agent, ...extra };
}
