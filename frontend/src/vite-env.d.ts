/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_SENTRY_DEBUG?: string;
  readonly VITE_APP_RELEASE?: string;
}
