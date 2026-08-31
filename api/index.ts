import express from "express";
import type { Express, Request, Response } from "express";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { registerOAuthRoutes } from "../server/_core/oauth.js";
import { registerStorageProxy } from "../server/_core/storageProxy.js";
import { appRouter } from "../server/routers.js";
import { createContext } from "../server/_core/context.js";

let appPromise: Promise<Express> | undefined;

export async function createApiApp() {
  const app = express();

  app.get("/api/health", (_req, res) => {
    res.json({
      status: "ok",
      service: "findwork-api",
      runtime: "vercel-node",
      configuration: {
        oauth: Boolean(process.env.OAUTH_SERVER_URL && process.env.VITE_APP_ID),
        session: Boolean(process.env.JWT_SECRET),
        database: Boolean(process.env.DATABASE_URL),
        storage: Boolean(
          process.env.BUILT_IN_FORGE_API_URL &&
            process.env.BUILT_IN_FORGE_API_KEY
        ),
      },
    });
  });

  app.use(express.json({ limit: "50mb" }));
  app.use(express.urlencoded({ limit: "50mb", extended: true }));
  registerStorageProxy(app);
  registerOAuthRoutes(app);
  app.use(
    "/api/trpc",
    createExpressMiddleware({
      router: appRouter,
      createContext,
    })
  );

  return app;
}

export default async function handler(req: Request, res: Response) {
  try {
    appPromise ??= createApiApp();
    const app = await appPromise;
    return app(req, res);
  } catch (error) {
    appPromise = undefined;
    console.error("[Vercel API] Initialization failed", error);
    return res.status(500).json({
      error: "api_initialization_failed",
      message: "The backend could not initialize. Check server-side environment variables.",
    });
  }
}
