import { test, expect } from "@playwright/test";

test("hosted reviewer keeps HTTPS and protected session boundaries", async ({
  page,
  context,
}) => {
  await page.goto("/");
  expect(new URL(page.url()).protocol).toBe("https:");
  const login = page.waitForResponse((response) =>
    response.url().endsWith("/api/auth/public-review"),
  );
  await page.getByRole("button", { name: "Explore read-only demo" }).click();
  await expect(page.getByLabel("Select portfolio")).toBeVisible();
  expect((await login).status()).toBe(200);
  const cookies = await context.cookies();
  const session = cookies.find((cookie) => cookie.name === "ledger_session");
  expect(session).toMatchObject({
    secure: true,
    httpOnly: true,
    sameSite: "Strict",
    path: "/",
  });
  expect(await page.evaluate(() => document.cookie)).not.toContain(
    "ledger_session",
  );
  const portfolios = await (await page.request.get("/api/portfolios")).json();
  expect(portfolios).toHaveLength(2);
  for (const portfolio of portfolios) {
    await page.getByLabel("Select portfolio").selectOption(portfolio.id);
    await expect(page.getByLabel("Select portfolio")).toHaveValue(portfolio.id);
    expect(
      (
        await page.request.get(`/api/portfolios/${portfolio.id}/ledger`)
      ).status(),
    ).toBe(200);
  }
  const identity = await (await page.request.get("/api/auth/me")).json();
  expect(identity.role).toBe("reviewer");
  const missingCsrf = await page.request.post("/api/auth/logout");
  expect(missingCsrf.status()).toBe(403);
  const wrongOrigin = await page.request.post("/api/auth/logout", {
    headers: {
      Origin: "https://untrusted.example.invalid",
      "X-CSRF-Token": identity.csrf,
    },
  });
  expect(wrongOrigin.status()).toBe(403);
  expect(
    (
      await page.request.get("/ready", {
        headers: { Host: "untrusted.example.invalid" },
      })
    ).status(),
  ).not.toBe(200);
  await page.request.post("/api/auth/logout", {
    headers: { "X-CSRF-Token": identity.csrf },
  });
});
