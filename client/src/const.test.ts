import { describe, expect, it } from "vitest";
import { buildOAuthLoginUrl } from "./const";
import { decodeOAuthState } from "@shared/const";

describe("buildOAuthLoginUrl", () => {
  it("builds a Manus OAuth URL bound to the current origin and nonce", () => {
    const origin = "https://find-work-tawny.vercel.app";
    const nonce = "nonce-for-test";
    const url = new URL(
      buildOAuthLoginUrl({
        origin,
        nonce,
        oauthPortalUrl: "https://manus.im",
        appId: "findwork-app",
      })
    );

    expect(url.origin).toBe("https://manus.im");
    expect(url.pathname).toBe("/app-auth");
    expect(url.searchParams.get("appId")).toBe("findwork-app");
    expect(url.searchParams.get("type")).toBe("signIn");

    const state = url.searchParams.get("state");
    expect(state).toBeTruthy();
    expect(decodeOAuthState(state ?? "")).toEqual({
      redirectUri: `${origin}/api/oauth/callback`,
      nonce,
    });
  });

  it("uses safe public defaults when Vercel build variables are absent", () => {
    const url = new URL(
      buildOAuthLoginUrl({
        origin: "https://find-work-tawny.vercel.app",
        nonce: "nonce-with-defaults",
      })
    );

    expect(url.origin).toBe("https://manus.im");
    expect(url.pathname).toBe("/app-auth");
    expect(url.searchParams.get("appId")).toBe("4L7zwPUhv2uYW7DPRnKywz");
  });
});
