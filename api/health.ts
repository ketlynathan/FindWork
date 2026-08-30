type NodeResponse = {
  statusCode: number;
  setHeader(name: string, value: string): void;
  end(body: string): void;
};

export default function handler(_request: unknown, response: NodeResponse) {
  response.statusCode = 200;
  response.setHeader("content-type", "application/json; charset=utf-8");
  response.end(
    JSON.stringify({
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
    })
  );
}
