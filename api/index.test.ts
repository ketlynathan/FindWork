import { createServer } from "node:http";
import { once } from "node:events";
import { describe, expect, it } from "vitest";
import { createApiApp } from "./index";

describe("Vercel API handler", () => {
  it("serves a health response from the serverless Express app", async () => {
    const app = await createApiApp();
    const server = createServer(app);

    server.listen(0, "127.0.0.1");
    await once(server, "listening");

    try {
      const address = server.address();
      if (!address || typeof address === "string") {
        throw new Error("Test server did not expose a TCP address");
      }

      const response = await fetch(`http://127.0.0.1:${address.port}/api/health`);
      const body = (await response.json()) as {
        status: string;
        service: string;
        runtime: string;
        configuration: Record<string, boolean>;
      };

      expect(response.status).toBe(200);
      expect(body.status).toBe("ok");
      expect(body.service).toBe("findwork-api");
      expect(body.runtime).toBe("vercel-node");
      expect(body.configuration).not.toHaveProperty("jwtSecret");
    } finally {
      server.close();
      await once(server, "close");
    }
  });
});
