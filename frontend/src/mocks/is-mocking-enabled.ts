export const MOCKING_ENABLED = process.env.NEXT_PUBLIC_API_MOCKING === "enabled";

export function isMockingEnabled(): boolean {
  return MOCKING_ENABLED;
}
