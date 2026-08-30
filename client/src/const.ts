import {
  encodeOAuthState,
  OAUTH_STATE_COOKIE,
} from "@shared/const";

export { COOKIE_NAME, ONE_YEAR_MS } from "@shared/const";

const DEFAULT_OAUTH_PORTAL_URL = "https://manus.im";
const DEFAULT_APP_ID = "4L7zwPUhv2uYW7DPRnKywz";

type OAuthLoginUrlOptions = {
  origin: string;
  nonce: string;
  oauthPortalUrl?: string;
  appId?: string;
};

/**
 * Build the Manus OAuth URL without side effects so the redirect contract can
 * be tested independently from the browser-only login handler.
 */
export const buildOAuthLoginUrl = ({
  origin,
  nonce,
  oauthPortalUrl = DEFAULT_OAUTH_PORTAL_URL,
  appId = DEFAULT_APP_ID,
}: OAuthLoginUrlOptions): string => {
  const redirectUri = `${origin}/api/oauth/callback`;
  const state = encodeOAuthState({ redirectUri, nonce });
  const url = new URL("/app-auth", oauthPortalUrl);

  url.searchParams.set("appId", appId);
  url.searchParams.set("redirectUri", redirectUri);
  url.searchParams.set("state", state);
  url.searchParams.set("type", "signIn");

  return url.toString();
};

// Start Manus OAuth from an event handler. This function has side effects: it
// mints a one-time nonce, writes the state cookie, and navigates immediately.
export const startLogin = () => {
  const oauthPortalUrl =
    import.meta.env.VITE_OAUTH_PORTAL_URL || DEFAULT_OAUTH_PORTAL_URL;
  const appId = import.meta.env.VITE_APP_ID || DEFAULT_APP_ID;
  const nonce = crypto.randomUUID();

  document.cookie = `${OAUTH_STATE_COOKIE}=${nonce}; Path=/; Max-Age=600; SameSite=None; Secure`;
  window.location.assign(
    buildOAuthLoginUrl({
      origin: window.location.origin,
      nonce,
      oauthPortalUrl,
      appId,
    })
  );
};
