import { defineConfig } from "@playwright/test";
import config from "./playwright.config";

const url = process.env.PLAYWRIGHT_BASE_URL;
if (!url || new URL(url).protocol !== "https:") {
  throw new Error(
    "Hosted verification requires an explicit HTTPS PLAYWRIGHT_BASE_URL",
  );
}
export default defineConfig({
  ...config,
  testMatch: ["**/*.public.ts", "**/*.hosted.ts"],
  use: { ...config.use, baseURL: url, ignoreHTTPSErrors: false },
});
