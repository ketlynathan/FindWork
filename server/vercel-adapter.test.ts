import { describe, expect, it } from "vitest";
import { createApp } from "./_core/index";

describe("Vercel server adapter", () => {
  it("creates the Express app without opening a local port", async () => {
    const previousNodeEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "test";

    try {
      const app = await createApp();
      expect(typeof app).toBe("function");
    } finally {
      if (previousNodeEnv === undefined) delete process.env.NODE_ENV;
      else process.env.NODE_ENV = previousNodeEnv;
    }
  });
});
