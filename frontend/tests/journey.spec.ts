import { test, expect } from "@playwright/test";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
const envPath = resolve("../.env");
const env = existsSync(envPath) ? readFileSync(envPath, "utf8") : "";
const password =
  process.env.DEMO_PASSWORD ?? env.match(/^DEMO_PASSWORD=(.+)$/m)?.[1];
if (!password) throw new Error("DEMO_PASSWORD required");

test("reviewer completes persisted import, evidence, review and billing journey", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "A clear view of your portfolio." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Integrations", exact: true }).click();
  await page.getByRole("button", { name: "snapshot.csv" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("quarantined");
  await page.getByRole("button", { name: "Replay this import" }).click();
  await expect(page.getByRole("status")).toContainText("Replay queued");
  await expect(page.locator("tbody tr").first()).toContainText("completed", {
    timeout: 20000,
  });
  await page.getByRole("button", { name: "snapshot.csv" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("7 duplicate");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Leases & ledger", exact: true })
    .click();
  await page.getByRole("button", { name: "Ledger", exact: true }).click();
  await page.locator("tbody tr button").first().click();
  await expect(page.getByRole("dialog")).toContainText("Content SHA-256");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .getByRole("button", { name: "Reconciliation", exact: true })
    .click();
  await page.locator("input[type=month]").fill("2026-11");
  await page.getByRole("button", { name: "Use current cutoff" }).click();
  await page
    .getByRole("button", { name: "Run reconciliation", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Reconciliation saved");
  await page.locator("tbody tr button").first().click();
  await page.getByLabel("Next status").selectOption("resolved");
  await page
    .getByLabel("Review rationale")
    .fill("Inspected synthetic source evidence; review creates no posting.");
  await page.getByRole("button", { name: "Save review" }).click();
  await expect(page.getByRole("status")).toContainText("Review recorded");
  await page
    .getByRole("button", { name: "Billing previews", exact: true })
    .click();
  await page.getByRole("button", { name: "Use current cutoff" }).click();
  await page.getByRole("button", { name: "Calculate preview" }).click();
  await expect(page.getByRole("dialog")).toContainText(/170[.,]00/);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  expect((await download).suggestedFilename()).toBe(
    "portfolioledger-2026-11.csv",
  );
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "A clear view of your portfolio." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Billing previews", exact: true })
    .click();
  await expect(page.locator("tbody tr").first()).toContainText(/170[.,]00/);
  await page
    .getByRole("button", { name: "Audit & operations", exact: true })
    .click();
  await expect(page.locator("tbody").first()).toContainText(
    "billing.preview_created",
  );
  await page
    .getByLabel("Select portfolio")
    .selectOption({ label: "Harbourlight Estates" });
  await page
    .getByRole("button", { name: "Leases & ledger", exact: true })
    .click();
  await page.getByRole("button", { name: "Ledger", exact: true }).click();
  await expect(page.locator("tbody")).toContainText("MER-E001");
});

test("mobile viewport remains usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "A clear view of your portfolio." }),
  ).toBeVisible();
  await expect(page.getByLabel("Select portfolio")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/mobile-overview.png",
    fullPage: true,
  });
});
