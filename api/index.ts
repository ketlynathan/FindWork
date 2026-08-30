import express from "express";
import type { Express, Request, Response } from "express";

let appPromise: Promise<Express> | undefined;

export async function createApiApp() {
  const [
    { createExpressMiddleware },
    { registerOAuthRoutes },
    { registerStorageProxy },
    { appRouter },
    { createContext },
  ] = await Promise.all([
    import("@trpc/server/adapters/express"),
    import("../server/_core/oauth"),
    import("../server/_core/storageProxy"),
    import("../server/routers"),
    import("../server/_core/context"),
  ]);

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
