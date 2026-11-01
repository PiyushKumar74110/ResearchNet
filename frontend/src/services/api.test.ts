import { describe, expect, it } from "vitest";

describe("ResearchMind frontend configuration", () => {
  it("has a default API base URL when no environment variable is configured", async () => {
    const { API_BASE } = await import("./api");
    expect(API_BASE).toMatch(/^https?:\/\//);
  });
});
