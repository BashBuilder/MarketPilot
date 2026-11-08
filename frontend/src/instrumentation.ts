export async function register(): Promise<void> {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  if (process.env.NEXT_PUBLIC_API_MOCKING !== "enabled") return;

  const { server } = await import("./mocks/server");
  server.listen();
}
