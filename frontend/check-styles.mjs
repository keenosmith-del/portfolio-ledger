import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
const css = readFileSync(new URL("./src/styles.css", import.meta.url), "utf8");
const tokens = new Set([
  "#ffffff",
  "#fafafb",
  "#f3f4f6",
  "#f6f7f8",
  "#1d1d1f",
  "#202124",
  "#646870",
  "#868a92",
  "#e5e7eb",
]);
for (const color of css.matchAll(/#[a-f\d]{3,8}\b/gi))
  assert(tokens.has(color[0].toLowerCase()), `Unapproved palette: ${color[0]}`);
const body = css.slice(css.indexOf("\n*"));
assert(!/#[a-f\d]{3,8}\b/i.test(body), "Component colors must use tokens");
assert(
  !/gradient|backdrop-filter|ArrowUpRight/.test(css),
  "Decorative legacy treatment",
);
assert(!/font-size:\s*(?:[7-9]|10)px/.test(css), "Unreadable small text");
assert(css.includes("prefers-reduced-motion"));
assert(
  /theme-color" content="#ffffff"/.test(
    readFileSync(new URL("./index.html", import.meta.url), "utf8"),
  ),
);
console.log("Neutral palette, token use, minimum type and motion guard passed");
