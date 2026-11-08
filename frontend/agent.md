# Frontend Agent: MarketPilot

You are the **Frontend Agent**. You own everything inside `frontend/`. You do NOT touch `backend/`. You build against the API contract in section 2, which is shared with the backend agent. If you need the contract to change, update section 2 in both `frontend/agent.md` and `backend/agent.md` in the same commit.

**Rule zero:** implement ONE step at a time. Finish its "Done when" criteria, commit, then move on. Never start step N+1 while step N is red.

You can work in parallel with the backend by running against a mock API (section 10, Step 1) until the real backend is ready.

---

## 1. Project Architecture

### 1.1 What the frontend does

Lets a user submit a campaign idea, watch the agents work live, review the generated campaign package (copy, visuals, compliance report, creative score), approve it or request a revision, and browse version history with diffs.

### 1.2 Stack

- Next.js 16.4.5 (App Router) with React 19.3 and TypeScript (`strict: true`)
- Tailwind CSS 4 and shadcn/ui (`base-nova` style, neutral base, CSS variables) on `@base-ui/react`, with the `cn` helper
- Recharts 3 for score visualizations
- Native `EventSource` for Server-Sent Events (SSE) live agent activity
- Zod 4 for runtime validation of API responses
- Node.js 22+ and `pnpm` (pinned as `pnpm@12.16.1`) only. No `npm` or `yarn` lockfiles
- Testing: Vitest 5 and React Testing Library for components, Playwright 1.64 with axe for end-to-end and accessibility, MSW 3 for API mocking (browser and Node)

`frontend/package.json` and `pnpm-lock.yaml` are the source of truth for exact versions.

### 1.3 Frontend layout

```
frontend/
  src/
    app/                      routes, layout, loading files, globals.css
      layout.tsx
      page.tsx                landing page
      campaigns/
        page.tsx              campaign list
        loading.tsx
        new/page.tsx          idea submission
        [id]/
          page.tsx            campaign overview (latest version)
          loading.tsx
          run/[runId]/page.tsx        live run view
          versions/page.tsx           version history and compare
          versions/loading.tsx
          versions/[n]/page.tsx       full package review and approval
          versions/[n]/loading.tsx
      style/                  design-token and shared-state reference
      api/assets/[...path]/   same-origin proxy for local backend images
      api/mock/campaigns/     mock-only browser-to-server campaign mirror
    components/
      agents/                 timeline, handoffs, tool calls, notices
      approval/               approve and revise panel and dialog
      campaign/               idea form and review cards
      landing/                landing-page sections
      layout/                 shell, header, navigation, container
      score/                  score breakdown chart (Recharts)
      states/                 empty, error, retry, skeleton states
      theme/                  early theme script and toggle
      ui/                     shadcn and base-ui primitives
      version/                version list, compare, diff, status
    lib/
      api/                    typed client, one function per endpoint
      assets/                 asset URL resolution and local-file safety
      design/                 token manifest and contrast helpers
      schemas/                Zod schemas mirroring the backend contract
      security/               CSP and header builder
      sse/                    stream hook, reducer, run-state types
      theme.ts
      utils.ts
    mocks/                    MSW handlers, fixtures, store, bridge
    test/                     Vitest setup and helpers
  e2e/                        Playwright specs and page list
  scripts/check-contract.ts
  ci/frontend-workflow.yml
  public/mockServiceWorker.js
  .env.example
  components.json
  next.config.ts
  playwright.config.ts
  vitest.config.mts
  package.json
```

Rule: components never call `fetch` directly. All network access goes through `lib/api` and `lib/sse`.

The finished project has no frontend `Dockerfile`, and the `frontend` service in `docker-compose.yml` is commented out. Add them only if you need container deployment. The app also deploys to Vercel with the project Root Directory set to `frontend`.

### 1.4 Routes

| Route                          | Purpose                                                |
| ------------------------------ | ------------------------------------------------------ |
| `/`                            | Landing page with pipeline preview and calls to action |
| `/campaigns`                   | Campaign list, newest first                            |
| `/campaigns/new`               | Idea form and example prompts                          |
| `/campaigns/[id]`              | Campaign overview and latest version                   |
| `/campaigns/[id]/run/[runId]`  | Live run view                                          |
| `/campaigns/[id]/versions`     | Version history and compare control                    |
| `/campaigns/[id]/versions/[n]` | Full package review and approval                       |
| `/style`                       | Design-token and shared-state reference                |
| `/api/assets/[...path]`        | Same-origin proxy for local backend images             |
| `/api/mock/campaigns`          | Mock-only browser-to-server campaign mirror            |

### 1.5 Commands

Run from `frontend/`.

| Command                                | Purpose                                              |
| -------------------------------------- | ---------------------------------------------------- |
| `pnpm install`                         | Install from `pnpm-lock.yaml`                        |
| `pnpm dev`                             | Dev server using `.env.local`                        |
| `pnpm dev:mock`                        | Dev server with `NEXT_PUBLIC_API_MOCKING=enabled`    |
| `pnpm dev:real`                        | Dev server pointed at `http://localhost:8000/api/v1` |
| `pnpm build` / `pnpm start`            | Production build and server                          |
| `pnpm lint`                            | ESLint                                               |
| `pnpm typecheck`                       | `next typegen && tsc --noEmit`                       |
| `pnpm test` / `pnpm test:watch`        | Vitest                                               |
| `pnpm test:e2e` / `pnpm e2e:mock`      | Playwright `mock` project                            |
| `pnpm e2e:real`                        | Playwright `real` project                            |
| `pnpm check:contract`                  | Validate live GET responses against Zod              |
| `pnpm audit --prod --audit-level=high` | Dependency audit                                     |

The standard check after every step is `pnpm test && pnpm lint && pnpm typecheck`, then `pnpm build` before committing. Run Playwright in Steps 10 and 11.

### 1.6 Configuration

Copy `.env.example` to `.env.local`; never commit the copy.

| Variable                  | Scope            | Purpose                                                                         |
| ------------------------- | ---------------- | ------------------------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL`     | Browser          | API base; default `http://localhost:8000/api/v1`                                |
| `NEXT_PUBLIC_API_MOCKING` | Browser and Node | Set to `enabled` by `pnpm dev:mock`                                             |
| `BACKEND_ASSET_DIR`       | Server only      | Directory for local backend images served by `/api/assets`; omit for Cloudinary |
| `E2E_API_URL`             | Test runner      | Real-backend Playwright URL; the `real` project is skipped when unset           |
| `CHECK_API_URL`           | Test runner      | Override for `pnpm check:contract`                                              |

Only `NEXT_PUBLIC_*` values reach the browser, and none may contain secrets. `NEXT_PUBLIC_*` values are inlined at build time, so changing one needs a rebuild.

### 1.7 Next.js 16 notes

- `next.config.ts` sets `cacheComponents: true` and `partialPrefetching: true`, plus the Turbopack `msw/browser` alias and the Tailwind CSS loader.
- Because `cacheComponents` is enabled, pages that fetch live data export `const instant = false` and `await params`.
- Route-level skeletons live in `src/app/campaigns/loading.tsx`, `[id]/loading.tsx`, `versions/loading.tsx` and `versions/[n]/loading.tsx`.
- Mock mode: `src/instrumentation.ts` starts MSW in Node when mocking is enabled; `MockProvider` mounts only when mocking is enabled; `/api/mock/campaigns` mirrors browser-created campaigns so Server Components can render their review pages. Mock mode must never be enabled in a production build.
- When a Next.js API is involved, read only the relevant guide in `node_modules/next/dist/docs/`. Do not browse the rest of `node_modules`.

### 1.8 Schema strictness (what the Zod schemas enforce)

These limits mirror what the finished frontend enforces. The backend is the source of truth: if a schema rejects real backend data, raise it under section 2 in both files instead of loosening only one side.

- `research.segments` are `{ name, description }`; `pain_points` and `messaging_angles` are lists; `sources` is required and only `http(s)` URLs become links.
- Asset `checksum` is 64 hex characters; `seed` is a non-negative integer with no safe-integer cap.
- `copy` and `assets` are wrapper objects (`copy.variants`, `assets.assets`).
- Each score dimension has `score` from 0 to 10 and a `justification` of 5 to 200 characters; `total` is 0 to 100.
- The idea form limits the idea to 2000 characters.

---

## 2. API Contract (shared with the backend agent)

Base path `/api/v1`, configured through `NEXT_PUBLIC_API_URL`. All bodies are JSON. Every response is parsed with a Zod schema in `lib/schemas`; a parse failure is surfaced as an error state, never silently ignored.

**Endpoints**

- `POST /campaigns` with `{ idea: string }` returns `{ campaign_id, run_id }`
- `GET /campaigns` returns `CampaignSummary[]`
- `GET /campaigns/{id}` returns one `CampaignSummary`
- `GET /campaigns/{id}/versions` returns `VersionSummary[]`, oldest first: `{ version, parent_version_id, score, created_at }`
- `GET /campaigns/{id}/versions/{n}` returns the full `CampaignPackage` for that version (no wrapper and no run metadata)
- `GET /campaigns/{id}/versions/{a}/diff/{b}` returns `{ from, to, changes: [{ path, before, after }] }`
- `POST /runs/{run_id}/approve` with `{ comment?: string }` returns `{ status: "completed", version }`
- `POST /runs/{run_id}/revise` with `{ comment: string, target_node?: string }` returns `{ run_id, version }`; `run_id` is the continuation run
- `GET /runs/{run_id}/stream` returns an SSE stream
- `GET /health` returns 200 at the root and under `/api/v1`

**Campaign summary shape** (items in `GET /campaigns` and the body of `GET /campaigns/{id}`)
`{ id, idea, status, latest_version: number | null, latest_score: number | null, active_run_id: string | null, created_at, updated_at }`

`status` is one of `draft`, `running`, `awaiting_approval`, `completed`, `failed`. `active_run_id` is the newest run that has not completed or failed.

**SSE events** (each has `id`, `event`, and JSON `data` with `run_id`, `timestamp`, `agent`)

- `agent_started`
- `agent_handoff` (from, to)
- `tool_called` (tool, duration_ms, status; status is `success`, `error`, or `denied`)
- `validation_failed` (reason)
- `retrying` (attempt, max_attempts)
- `awaiting_approval` (version)
- `completed` (version, score; score may be null)
- `error` (message, recoverable)

`agent` is one of the eight pipeline agents (`brief`, `research`, `copywriter`, `creative_director`, `designer`, `compliance`, `reviewer`, `supervisor`) or `human` for the approval gate and completion. Handoffs may target `human`.

**Stream behavior**

- The `id` of each SSE event is opaque and increasing; clients send the last one back as `Last-Event-ID`.
- The server closes the stream after a terminal event: `awaiting_approval`, `completed`, or `error` with `recoverable: false`.
- Clients must not reconnect after a terminal event. They reconnect only after an unexpected drop.
- On an unexpected drop the client leaves the `EventSource` open so the browser reconnects natively and sends `Last-Event-ID` automatically. It must not close and reopen with a query parameter, and it must not create a second connection.
- An open stream that stays silent for a generous window (default 75s) shows a bounded no-progress state with a reload action. A slow model call is not an error.

**Package shape (per version):**

A version may be snapshotted at the human gate before every agent finishes. The backend serializes it with `response_model_exclude_none`, so an unproduced section arrives either as `null` or omitted entirely. The UI must render an explicit per-section "not produced" state in both cases; it must not reject the whole package or drop the field.

- `brief`: `{ product, goal, audience, tone, channels, constraints } | null`
- `research`: `{ segments, pain_points, messaging_angles, sources } | null`, sources are `{ title, url }`
- `copy`: `{ variants } | null`, each variant is `{ channel, headline, description, cta }`
- `direction`: `{ style_guide, composition, image_prompts, video_prompts, negative_prompts } | null`
- `assets`: `{ assets } | null`, each asset is `{ uri, checksum, model, seed, prompt }`
- `compliance`: `{ items } | null`, each item is `{ check, passed, reason }`
- `score`: five dimensions (`brief_alignment`, `audience_fit`, `copy_quality`, `visual_quality`, `compliance_risk`), each `{ score, justification }`, plus `total`; the whole score is `null` until the Reviewer produces it

Asset `seed` is a 64-bit integer and may exceed `Number.MAX_SAFE_INTEGER`. JSON clients receive an imprecise `Number`, so validate it as a non-negative integer without enforcing the safe-integer cap; never reject the package because of a large seed.

**Errors:** `{ error: { code, message, details? } }` with the matching HTTP status.

---

## 3. Coding Conventions

- TypeScript `strict: true`. No `any`. No non-null assertions without a comment explaining why.
- Zod schemas are the source of truth for API types; derive TypeScript types with `z.infer`.
- Server Components by default. Use Client Components only for interactivity: the SSE feed, approval controls, diff toggles.
- Data fetching in Server Components where possible; client-side fetching for live and mutating views.
- shadcn/ui primitives first; build custom components only when no primitive fits. Read the project's own primitives (`src/components/ui/*.tsx`) before guessing a library API. Style with Tailwind tokens, no arbitrary one-off values scattered around.
- One component per file, named exports, props typed with an explicit interface.
- Accessibility is part of the code, not a later pass: semantic HTML, labels on inputs, keyboard-operable controls, visible focus, sufficient contrast, `aria-live` on the agent activity feed.
- ESLint and Prettier clean. Conventional commits (`feat:`, `fix:`, `test:`, `chore:`).

---

## 4. Agent Responsibilities (what the UI must represent)

The UI mirrors the backend pipeline. Each agent has a clear visual identity (name, short description, status) in the live timeline.

- **Brief, Research, Copywriter, Creative Director, Designer, Compliance, Reviewer, Supervisor.** Show each as a step in the timeline with states: waiting, running, retrying, failed, done.
- Show handoffs between agents as they arrive (`agent_handoff`).
- Show tool calls compactly (tool name, duration, status) and expandable for details.
- Show validation failures and retries honestly, including attempt counts. Do not hide failures.
- When the stream is open but silent, show the bounded no-progress state instead of an indefinite "waiting" message. A slow model call is not a failure.
- At `awaiting_approval`, the approval panel becomes the focus of the page.

**Review screen must show:** brief, audience research, copy variants per channel, image assets with prompt, model and seed on demand, the compliance report (pass/fail per item with reason), and the creative score with per-dimension breakdown and justification.

---

## 5. Tool and Action Permissions

The frontend only does what a signed-in user is allowed to do through the API.

- Allowed: create campaign, view campaigns and versions, stream a run, approve, request a revision, view diffs.
- Not allowed: calling any endpoint not in section 2, triggering export without a recorded approval, or exposing any backend secret.
- Approve and Revise are destructive-ish actions: require an explicit confirm step, disable the buttons while the request is in flight, and prevent double submission.
- Revision requires a non-empty comment; `target_node` is optional and limited to the agent names the backend lists.

---

## 6. Data and State Rules

- Server state (campaigns, versions) comes from the API; do not duplicate it in global client stores. Use a small query layer with caching and invalidation after mutations (approve, revise).
- Live run state is derived from the SSE event stream with a reducer; it is a pure function of the ordered events so it can be replayed in tests.
- The SSE hook must handle: connection drop, native reconnect with `Last-Event-ID` (no manual close and reopen), duplicate events (dedupe by event id), a bounded stall/no-progress state, and cleanup on unmount.
- Never store anything sensitive in `localStorage`. Only UI preferences may be persisted there (the theme uses the key `marketpilot-theme`).
- Images are loaded from backend asset URIs. Hosted assets are absolute Cloudinary `https://res.cloudinary.com` URLs and load directly; the CSP allows that image origin. Backend-relative file names go through the same-origin `/api/assets` proxy, which reads the directory configured by the server-only `BACKEND_ASSET_DIR`. Always provide `alt` text from the creative direction and a fallback state if an image fails to load.

---

## 7. Testing Requirements

- **Schemas:** every Zod schema has a test with a valid fixture and at least one invalid fixture.
- **Components:** agent timeline states, approval panel (confirm, in-flight, error), score chart, diff view, empty, loading and error states.
- **SSE hook and reducer:** event ordering, duplicate events, reconnect with `Last-Event-ID`, malformed event handling, the 75s stall state, unmount cleanup.
- **API client:** MSW-based tests for success, validation failure (bad payload shape) and HTTP error responses.
- **End-to-end (Playwright):** two projects. The `mock` project (port 3000) runs `happy-path.spec.ts`, `accessibility.spec.ts`, `responsive.spec.ts` and `security-headers.spec.ts`, using the page list in `e2e/pages.ts`. The `real` project (port 3001) runs only when `E2E_API_URL` is set and matches only the happy path. Verify the revise flow (submit, revise with a comment and target node, follow the continuation run, see version N+1 and the diff) manually against the real backend.
- **Accessibility:** automated axe checks on every page in `appPages`, in light and dark themes, with zero serious or critical violations.
- **Responsive:** assert no horizontal overflow at 360, 768 and 1280 px.
- **Contract:** `pnpm check:contract` validates every live GET response against the Zod schemas.
- Coverage: at least 80% on `lib/` and reducers.

---

## 8. Security Restrictions

- Only `NEXT_PUBLIC_*` variables reach the browser, and only non-secret ones. No API keys in the frontend, ever.
- Render all backend text (copy, research, justifications) as text. No `dangerouslySetInnerHTML` on backend content. Only `http(s)` source URLs become links, with `rel="noopener noreferrer"`.
- Validate every response with Zod before use. Treat parse failure as an error state.
- Validate forms client-side (idea length limit) but never rely on that alone; show backend validation errors clearly.
- Set security headers in `next.config` through `src/lib/security/headers.ts`: CSP with `default-src 'self'` and `frame-ancestors 'none'`; `img-src` allowing self, the API origin, `https://res.cloudinary.com`, `data:` and `blob:`; `connect-src` allowing self plus the API origin only (do not widen it for assets); `ws:`/`wss:` and `unsafe-eval` only in development. Also `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` and `X-Frame-Options: DENY`.
- The local asset proxy keeps paths inside `BACKEND_ASSET_DIR`, resolves symlinks before containment checks, serves only supported image types, and returns 404 when unconfigured.
- Do not log tokens, full prompts or user content to the console in production builds.
- Pin dependencies through `pnpm-lock.yaml`; run `pnpm audit --prod --audit-level=high` in CI.
- If a Dockerfile is added: non-root user, multi-stage build, no secrets baked into the image.

---

## 9. Design Direction

Design taste is a stated bonus for the role this project supports, so treat it as a requirement.

- Editorial, calm and confident. One restrained palette (a warm neutral base plus a single teal accent, `--brand`, the only saturated colour), a consistent type scale and a consistent 4px spacing scale.
- The generated creative is the hero: give assets and copy room, keep chrome quiet.
- Subtle motion only where it carries meaning: an agent handoff, a score settling. Respect `prefers-reduced-motion`.
- Every view has designed empty, loading (skeletons) and error states.
- Responsive from mobile to wide desktop. Light and dark themes with correct contrast in both.

---

## 10. Implementation Workflow (step by step)

Work strictly in order. Each step: goal, tasks, done when.

The build playbook groups these steps into phases: Phase 0 is Step 0, Phase 1 is Step 1, Phase 2 is Step 2, Phase 3 is Steps 3 to 5, Phase 4 is Steps 6 and 7, Phase 5 is Steps 8 and 9, Phase 6 is Step 11, and Phase 7 is Step 10 plus the final check. Step 11 does not need the backend, so it can run before Step 10.

### Step 0: Project bootstrap

- Start from an empty `frontend/`: `pnpm create next-app@latest . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm`, then `pnpm dlx shadcn@latest init` (base-nova, neutral, CSS variables), then `pnpm dlx msw init public --save`.
- Add shadcn components `button`, `textarea`, `label`, `field`, `dialog`, `separator`.
- Dependencies: `next@16.4.5`, `react@19.3.0`, `react-dom@19.3.0`, `recharts`, `zod`, `@base-ui/react`, `class-variance-authority`, `cn`, `lucide-react`, `shadcn`, `tw-animate-css`. Dev dependencies: Vitest, Testing Library, MSW, Playwright, axe, `cross-env`, `jsdom`, `tsx`, the Tailwind Turbopack plugin, `@vitejs/plugin-react` and coverage packages. Match the versions in `package.json`.
- Scripts exactly as in section 1.5; `packageManager` is `pnpm@12.16.1`. Keep `msw.workerDirectory: ["public"]`.
- `next.config.ts` as in section 1.7. `tsconfig.json` with `strict`, `moduleResolution: "bundler"`, `paths`, and `.next/dev/types` included. `vitest.config.mts` with jsdom, the `@` alias, a setup file, and `e2e/**` excluded. `playwright.config.ts` with the `mock` and `real` projects.
- `.env.example` with `NEXT_PUBLIC_API_URL`, optional `BACKEND_ASSET_DIR`, and the `NEXT_PUBLIC_API_MOCKING` switch.
- A Dockerfile and the `docker-compose.yml` frontend service are optional and deferred to Step 11.
- **Done when:** `pnpm install`, `pnpm dev`, `pnpm lint`, `pnpm typecheck` and `pnpm build` succeed, and no secret or `.env.local` is committed.

### Step 1: Contract layer and mock API

- `src/lib/schemas/`: `common.ts`, `campaign.ts`, `runs.ts`, `package.ts`, `sse.ts`, `errors.ts`, `index.ts`. Derive every TypeScript type with `z.infer`. Follow section 1.8.
- `src/lib/api/`: `client.ts` (with `API_BASE_URL`, `ApiError`, and one `apiRequest(path, schema, options)` helper using `cache: "no-store"` that handles JSON, network, status and Zod failures), `campaigns.ts`, `runs.ts`, `health.ts`, `index.ts`.
- `src/mocks/`: fixtures for the hair-care package (all sections, three passing compliance checks, one asset, five score dimensions), campaign and run summaries, scripted SSE (happy path, retry, validation failure, awaiting approval), revision package and diff; plus `handlers.ts`, `store.ts`, `run-actions.ts`, `bridge.ts`, `browser.ts`, `server.ts`, `provider.tsx`.
- `src/instrumentation.ts` starts MSW in Node when mocking is enabled; `src/app/api/mock/campaigns/route.ts` mirrors browser-created campaigns.
- MSW handlers cover every endpoint, including approve, revise, stream, and a catch-all JSON 404. Approve sets `completed`; revise creates version N+1 with `parent_version_id`, a new run, and a diff.
- **Done when:** schema tests pass (each with a valid and an invalid fixture), API client tests cover success, bad payload and HTTP error, `pnpm dev:mock` renders the seeded campaign and its version, and the scripted run reaches `awaiting_approval`.

### Step 2: Design system foundation

- `src/app/globals.css`: warm neutral palette, one teal accent (`--brand`), light and dark tokens, 4px spacing scale, editorial type scale, radii, chart ramp, semantic shadcn tokens.
- `src/lib/design/token-manifest.ts` and `contrast.ts`, with tests that check text and background contrast in both themes.
- `src/lib/theme.ts`: system preference, `localStorage` key `marketpilot-theme`, cross-tab sync, and a pre-paint init script used by `ThemeScript` and `ThemeToggle`.
- `src/components/layout/`: `page-container.tsx`, `site-header.tsx`, `site-nav.tsx`, `skip-link.tsx`. The root `layout.tsx` includes the font, skip link, header, main landmark, and `MockProvider` only when mocking is enabled.
- `src/components/states/`: `empty-state.tsx`, `error-state.tsx`, `retry-error-state.tsx`, `skeleton-block.tsx`, `heading-level.ts`.
- `/style` renders tokens and all three states in fixed light and dark panels.
- **Done when:** `/style` renders every token and state in both themes, contrast tests pass, and the shell is keyboard accessible.

### Step 3: SSE hook and run reducer

- `src/lib/sse/run-state.ts`: `AGENT_ORDER`, agent statuses (`waiting`, `running`, `retrying`, `failed`, `done`), run statuses, handoffs, tool calls, errors, malformed events, event ids, version and score.
- `src/lib/sse/reducer.ts`: pure `applySseEvent` and `applySseEvents`; dedupe by event id; mark the handoff source done; handle retries, validation failures, approval, completion and recoverable errors.
- `src/lib/sse/useRunStream.ts`: open `API_BASE_URL + /runs/{id}/stream`; validate each event with the Zod schemas; record malformed frames instead of throwing; close on terminal events; rely on native reconnect after an unexpected drop; flag 75s of silence as stalled; clean up on unmount.
- **Done when:** tests cover ordering, duplicates, native reconnect, the bounded stall state, malformed events and cleanup.

### Step 4: New campaign flow

- `src/components/campaign/`: `IdeaForm.tsx`, `ExamplePrompts.tsx`, `example-prompts.ts`. The idea limit is 2000 characters; show a counter, inline errors, a disabled submit while pending, `Cmd/Ctrl+Enter`, and three example ideas including the hair-care brief.
- `/campaigns/new` calls `createCampaign`, shows `ApiError` in `ErrorState`, prevents double submit, and routes to `/campaigns/{id}/run/{runId}`.
- **Done when:** submission works against the mock, shows loading and error states, and prevents double submit.

### Step 5: Live run view

- `src/components/agents/`: `AgentTimeline.tsx`, `StatusBadge.tsx`, `HandoffNote.tsx`, `ToolCallFeed.tsx`, `FailureNotice.tsx`, `RunFailureList.tsx`, `RunApprovalPrompt.tsx`, `agent-meta.ts`, `agent-format.ts`.
- `live-run-view.tsx`: status headline, connecting and reconnecting indicator, stalled state with reload, fatal error state, malformed-event warning, approval prompt, timeline, retries, handoffs and tool calls, with `aria-live` updates.
- **Done when:** replaying the scripted mock run shows every state correctly, and component tests pass.

### Step 6: Review screen

- Review cards: `BriefCard`, `ResearchCard`, `CopyCard`, `AssetGrid`, `ComplianceReport`, `ScoreBreakdown`.
- `ResearchCard` shows segments, top-level pain points, messaging angles, and safe `http(s)` source links. `CopyCard` receives `copy?.variants` and groups variants by channel. `AssetGrid` receives `assets?.assets`, resolves hosted and local URLs with `resolveAssetUrl`, uses creative direction for alt text, shows a fallback on load failure, and reveals prompt, model and seed in a details disclosure. `ComplianceReport` shows `{ check, passed, reason }` with words and icons, not colour alone. `ScoreBreakdown` uses Recharts for the five fixed dimensions and the total, includes a text alternative, and does not animate.
- `/campaigns/[id]/versions/[n]` loads the campaign, version list and package; handles invalid or missing versions; renders an `EmptyState` for each missing section; keeps a loading skeleton.
- **Done when:** every section renders from a fixture package, including failed compliance items, missing images, and `null` sections from a partially produced version.

### Step 7: Approval and revision

- `src/components/approval/`: `ApprovalPanel.tsx`, `ApprovalDialog.tsx`, `ApprovalFields.tsx`, `VersionApproval.tsx`. Approve has an optional comment; revise requires a non-empty comment and offers an optional target node from the eight agents. Require an explicit confirm, disable controls while pending, and show errors with `ErrorState`.
- `VersionApproval` only renders for the latest `awaiting_approval` version with an `active_run_id`. Approve calls `approveRun`, shows the approved state and refreshes; revise calls `reviseRun` and routes to the continuation run. After a mutation, invalidate queries.
- **Done when:** approve and revise flows work against the mock, handle HTTP errors, and cannot double submit.

### Step 8: Version history and diff

- `/campaigns/[id]/versions`: `VersionList` sorts newest first (the API returns oldest first), marks revisions, links to each review page, and has empty and error states. `VersionCompare` picks two versions and calls the diff endpoint. `DiffView` groups changes by package section and shows before and after with a "Changed" label, never colour alone.
- **Done when:** a revised campaign shows version N and N+1 with correct highlighted changes.

### Step 9: Campaign list, overview and landing page

- `/campaigns`: Server Component list with newest-first sorting, `CampaignCard`, an empty state with a create link, a retry error state, and `loading.tsx`. `StatusPill` shows campaign status.
- `/campaigns/[id]`: `CampaignOverview` shows the idea, latest version score and status, links to review and history, and an active-run notice.
- `/`: landing page with the pipeline preview, highlights, and closing calls to action.
- Server pages that fetch live data export `const instant = false` and `await params`.
- **Done when:** list, overview and landing pages have loading, empty, error and populated states, and the 404 state works.

### Step 10: Integrate with the real backend

- Set `NEXT_PUBLIC_API_URL` in `.env.local` (or use `pnpm dev:real`). Start the backend in fake mode from `backend/`: `APP_MODE=fake uv run uvicorn app.main:app --reload`.
- Run `pnpm check:contract`. Fix only genuine frontend schema drift; if the backend changed the contract, stop and update section 2 in both files first.
- Run the real happy path: `E2E_API_URL=http://localhost:8000/api/v1 pnpm e2e:real`. Then verify the revise flow manually (see section 7).
- Do not change backend code. If a contract mismatch is real, report it before editing either guide.
- **Done when:** the contract checker passes, the real happy path reaches approval, a manual revision produces a new version and a diff, and idea to approval works end to end against the real backend running in fake mode.

### Step 11: Polish, accessibility and hardening

- Security headers and the local asset proxy as in sections 6 and 8: `src/lib/security/headers.ts`, `src/lib/assets/asset-url.ts`, `src/lib/assets/local-file.ts`, and `src/app/api/assets/[...path]/route.ts`.
- Playwright specs as in section 7 (`happy-path`, `accessibility`, `responsive`, `security-headers`, plus `e2e/pages.ts`). Motion respects `prefers-reduced-motion`; `aria-live` stays on live regions.
- `ci/frontend-workflow.yml`: pnpm install, lint, typecheck, Vitest, build, Playwright mock, and the production audit. The root CI copy lives in `.github/workflows/` and is moved there outside `frontend/`.
- `frontend/README.md`: requirements, setup, scripts, mock versus real mode, folder map, tests and CI.
- Keep `.env.local` out of git; add it (and Playwright output if needed) to the root `.gitignore` if the checkout does not already cover it.
- **Done when:** `pnpm build` passes, `pnpm e2e:mock` passes (happy path, axe light and dark, responsive widths, headers), asset URL and local-file safety tests pass, `pnpm audit --prod --audit-level=high` passes, and a fresh clone reaches the demo flow in under 10 minutes following the README.

---

## 11. Definition of Done

A step is done only when all of these hold:

1. Code follows section 3 and no component calls the network outside `lib/api` and `lib/sse`.
2. Every API response is validated with Zod; every view has loading, empty and error states.
3. Tests pass at the levels in section 7, including accessibility checks for new pages.
4. `pnpm lint`, `pnpm typecheck` (`next typegen && tsc --noEmit`) and `pnpm build` report zero errors.
5. No security restriction in section 8 is violated.
6. The UI matches the design direction in section 9, in light and dark themes and on mobile.
7. The API contract in section 2 is unchanged, or updated in both agent files.
8. Docs updated, conventional commit made, CI green.
9. The step's own "Done when" criteria are demonstrably met.
10. From Step 10 onward, `pnpm check:contract` reports no failures against the running backend.
