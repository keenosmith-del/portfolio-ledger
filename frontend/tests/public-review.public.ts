import { test, expect } from "@playwright/test";

async function closeWithEscape(page: import("@playwright/test").Page) {
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).focus();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
}

test.use({ viewport: { width: 1440, height: 900 } });

test("public reviewer browses evidence and CSV with all direct business writes denied", async ({
  page,
}) => {
  await page.goto("/");
  expect((await page.request.get("/ready")).status()).toBe(200);
  await page.getByRole("button", { name: "Explore read-only demo" }).click();
  await expect(page.getByLabel("Select portfolio")).toBeVisible();
  const portfolios = await page.request.get("/api/portfolios");
  expect(portfolios.status()).toBe(200);
  const [{ id }] = await portfolios.json();
  const identity = await (await page.request.get("/api/auth/me")).json();
  expect(identity.role).toBe("reviewer");
  const base = `/api/portfolios/${id}`;
  await page.getByRole("button", { name: "Integrations", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Queue import" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "snapshot.csv" }).first().click();
  await expect(
    page.getByRole("button", { name: "Replay this import" }),
  ).toHaveCount(0);
  await closeWithEscape(page);
  await page
    .getByRole("button", { name: "Leases & ledger", exact: true })
    .click();
  await page.getByRole("button", { name: "Ledger", exact: true }).click();
  await page.locator("tbody tr button").first().click();
  await expect(page.getByRole("dialog")).toContainText("Content SHA-256");
  await closeWithEscape(page);
  await page
    .getByRole("button", { name: "Reconciliation", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run reconciliation", exact: true }),
  ).toBeDisabled();
  await page.locator("tbody tr button").first().click();
  await expect(page.getByRole("button", { name: "Save review" })).toHaveCount(
    0,
  );
  await closeWithEscape(page);
  await page
    .getByRole("button", { name: "Billing previews", exact: true })
    .click();
  await page.locator("tbody tr button").first().click();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  expect((await download).suggestedFilename()).toContain("portfolioledger-");
  const jobs = await (await page.request.get(base + "/imports")).json();
  const exceptions = await (
    await page.request.get(base + "/exceptions")
  ).json();
  for (const suffix of [
    "/reconciliations",
    "/billing-previews",
    `/imports/${jobs.items[0].id}/replay`,
    `/exceptions/${exceptions.items[0].id}/resolve`,
  ]) {
    const result = await page.request.post(base + suffix, {
      headers: {
        "X-CSRF-Token": identity.csrf,
        "Idempotency-Key": "public-denied",
      },
      data: {
        month: "2026-11",
        cutoff: new Date().toISOString(),
        status: "resolved",
        rationale: "Public write attempt must be rejected",
      },
    });
    expect(result.status(), suffix).toBe(403);
  }
  const upload = await page.request.post(base + "/imports", {
    headers: {
      "X-CSRF-Token": identity.csrf,
      "Idempotency-Key": "public-upload-denied",
    },
    multipart: {
      adapter: "atlaspm",
      source_key: "atlaspm-demo",
      file: {
        name: "snapshot.csv",
        mimeType: "text/csv",
        buffer: Buffer.from("synthetic"),
      },
    },
  });
  expect(upload.status()).toBe(403);
  await closeWithEscape(page);
  await page
    .getByRole("button", { name: "Audit & operations", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Execution & audit timeline" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Refresh", exact: true }),
  ).toBeEnabled();
  await expect(
    page
      .locator(".panel")
      .filter({
        has: page.getByRole("heading", { name: "Execution & audit timeline" }),
      })
      .locator("tbody tr")
      .first(),
  ).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: "../docs/evidence/ui/after/public-review-audit.png",
    fullPage: true,
  });
});

// Closing a browser context does not revoke its server session. Keep repeated QA bounded.
test.afterEach(async ({ page }) => {
  const response = await page.request.get("/api/auth/me");
  if (response.ok()) {
    const identity = await response.json();
    await page.request.post("/api/auth/logout", {
      headers: { "X-CSRF-Token": identity.csrf },
    });
  }
});
