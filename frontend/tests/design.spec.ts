import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { existsSync, readFileSync } from "node:fs";
const env = existsSync("../.env") ? readFileSync("../.env", "utf8") : "";
const password =
  process.env.DEMO_PASSWORD ?? env.match(/^DEMO_PASSWORD=(.+)$/m)?.[1];
if (!password) throw new Error("Private demo password required");
const tabs = [
  "Overview",
  "Integrations",
  "Leases & ledger",
  "Reconciliation",
  "Billing previews",
  "Audit & operations",
];

async function login(
  page: import("@playwright/test").Page,
  email = "admin@portfolioledger.test",
) {
  await page.goto("/");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password!);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByLabel("Select portfolio")).toBeVisible();
}

test("search, empty state, keyboard dialog containment and session persistence", async ({
  page,
}) => {
  await login(page);
  await page
    .getByRole("button", { name: "Leases & ledger", exact: true })
    .click();
  const search = page.getByRole("textbox", { name: "Search leases" });
  await search.fill("NO-SUCH-REFERENCE");
  await expect(page.getByText("No records match this view.")).toBeVisible();
  await search.fill("ATL-L001");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await search.fill("");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await page.getByRole("button", { name: "Ledger", exact: true }).click();
  const trigger = page.locator("tbody tr button").first();
  await trigger.focus();
  await page.keyboard.press("Enter");
  const close = page.getByRole("button", { name: "Close dialog" });
  await expect(close).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(
    await page.evaluate(
      () => !!document.activeElement?.closest("[role=dialog]"),
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await page.reload();
  await expect(page.getByLabel("Select portfolio")).toBeVisible();
});

test("all views fit six widths with readable controls and region scrolling", async ({
  page,
}) => {
  await login(page);
  for (const width of [320, 390, 430, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const name of tabs) {
      await page.getByRole("button", { name, exact: true }).click();
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await expect
        .poll(() => page.evaluate(() => document.documentElement.scrollWidth))
        .toBeLessThanOrEqual(width);
      const undersized = await page
        .locator("input:not([type=hidden]),select,.button,.icon-button")
        .evaluateAll((nodes) =>
          nodes
            .filter((n) => {
              const r = n.getBoundingClientRect();
              return r.width > 0 && r.height > 0 && r.height < 40;
            })
            .map((n) => n.outerHTML.slice(0, 120)),
        );
      expect(undersized).toEqual([]);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("button", { name: "Leases & ledger", exact: true })
    .click();
  expect(
    await page
      .locator(".table-scroll")
      .evaluate((n) => n.scrollWidth > n.clientWidth),
  ).toBe(true);
  await expect(
    page.getByRole("button", { name: "Sign out", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
});

test("login and all operational screens pass WCAG AA automated audit", async ({
  page,
}) => {
  await page.goto("/");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await login(page);
  for (const name of tabs) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const result = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(result.violations, name).toEqual([]);
  }
});

test("private reviewer can inspect evidence and export but cannot write", async ({
  page,
}) => {
  await login(page, "reviewer@portfolioledger.test");
  await page.getByRole("button", { name: "Integrations", exact: true }).click();
  await expect(page.getByLabel("Source file")).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Queue import" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "snapshot.csv" }).first().click();
  await expect(page.getByRole("dialog")).toContainText("duplicate");
  await expect(
    page.getByRole("button", { name: "Replay this import" }),
  ).toHaveCount(0);
  await page.keyboard.press("Escape");
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
  await page.keyboard.press("Escape");
  await page
    .getByRole("button", { name: "Billing previews", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Calculate preview" }),
  ).toBeDisabled();
  await page.locator("tbody tr button").first().click();
  await expect(page.getByRole("dialog")).toContainText(/170[.,]00/);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  expect((await download).suggestedFilename()).toContain("portfolioledger-");
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
