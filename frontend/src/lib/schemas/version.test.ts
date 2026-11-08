import { describe, expect, it } from "vitest";
import {
  ApproveResponseSchema,
  ReviseRequestSchema,
  VersionDiffSchema,
  VersionSummarySchema,
} from "./version";

const validVersion = {
  version: 2,
  parent_version_id: "aaaaaaaa-1111-4111-8111-111111111111",
  score: 81.5,
  created_at: "2026-01-02T09:30:00Z",
};

describe("VersionSummarySchema", () => {
  it("accepts a valid version summary", () => {
    expect(VersionSummarySchema.parse(validVersion)).toEqual(validVersion);
  });

  it("accepts a first version with no parent and no score", () => {
    const parsed = VersionSummarySchema.parse({
      ...validVersion,
      version: 1,
      parent_version_id: null,
      score: null,
    });
    expect(parsed.parent_version_id).toBeNull();
  });

  it("rejects a zero version number", () => {
    expect(() => VersionSummarySchema.parse({ ...validVersion, version: 0 })).toThrow();
  });
});

describe("VersionDiffSchema", () => {
  it("accepts a diff with changes", () => {
    const diff = {
      from: 1,
      to: 2,
      changes: [{ path: "copy.variants[0].headline", before: "Old", after: "New" }],
    };
    expect(VersionDiffSchema.parse(diff)).toEqual(diff);
  });

  it("rejects a change without a path", () => {
    expect(() =>
      VersionDiffSchema.parse({ from: 1, to: 2, changes: [{ before: "a", after: "b" }] }),
    ).toThrow();
  });
});

describe("ApproveResponseSchema", () => {
  it("accepts the completed status", () => {
    expect(ApproveResponseSchema.parse({ status: "completed", version: 1 }).version).toBe(1);
  });

  it("rejects any other status", () => {
    expect(() => ApproveResponseSchema.parse({ status: "running", version: 1 })).toThrow();
  });
});

describe("ReviseRequestSchema", () => {
  it("accepts a comment with an optional target node", () => {
    expect(
      ReviseRequestSchema.parse({ comment: "Sharper headline", target_node: "copywriter" }).comment,
    ).toBe("Sharper headline");
  });

  it("rejects an empty comment", () => {
    expect(() => ReviseRequestSchema.parse({ comment: "  " })).toThrow();
  });

  it("rejects a target node outside the eight pipeline agents", () => {
    expect(() =>
      ReviseRequestSchema.parse({ comment: "Sharper headline", target_node: "intern" }),
    ).toThrow();
  });
});
