# Engineering journal

Entries are recorded during work. This is an account of observed activity, not a reconstructed commit history. Times are UTC; reviewer-facing calendar context is Africa/Johannesburg (UTC+02).

## 2026-11-11 — Initial reconnaissance and foundation (recorded 07:02 UTC)

Starting state: commit `346d1dd` on `main`, clean working tree, one 19-byte README. Remote: `https://github.com/keenosmith-del/portfolio-ledger.git`. No applicable AGENTS.md found. Read the entire supplied master build prompt. Python default was 3.15.1; selected installed Python 3.12 for compatibility. Node 24.21.0, npm 11.19.0, Docker CLI 29.8.2. Checked environment variable names only; no secret values printed.

Objective: establish a PostgreSQL-first, explicitly transactional foundation and durable ingestion primitives before adding UI.

Changes: Python package, typed ORM models, adapter validation, financial helpers, authentication dependencies, source-scoped ingestion serialization, queue worker, finance services, Compose, Dockerfile, environment example. These are implementation in progress, not accepted product behavior.

Observed failures and corrections:
- First dependency installation failed because restricted execution could not resolve pypi.org. Re-ran with approved network access; installation succeeded.
- Docker engine initially stopped. `open -a Docker` failed to locate the application; explicit `/Applications/Docker.app` launched with approved access.
- First Compose invocation failed before creating resources because DEMO_PASSWORD was required. Generated a private local `.env` with a random password and mode 0600; no password committed or printed. Local PostgreSQL container then started.
- First Ruff pass fixed four import/unused-import issues; formatted ten files. Strict mypy passed for 12 source files. These are static checks only; no database tests had run at this entry.

Design decisions: ADR-001 and ADR-002. Initial migration generation started against actual PostgreSQL. Documentation requirement was added by the owner during this increment; this is the first journal entry and explicitly includes work preceding that instruction. No earlier journal entries or commits are invented.

Verification status: static typing passes. Migration, database behavior, browser workflow and performance remain pending. See iteration 001 and the evidence index.

### Foundation verification and first saved increment

Generated initial Alembic revision against the empty local PostgreSQL database; added a separate immutability-trigger revision. Applied both with exit 0. Seven financial boundary/CSV-safety tests passed in 0.04s. Ruff and strict mypy passed. Saving this verified infrastructure increment; import, HTTP, concurrency and full UI verification remain outstanding. No failed-to-passing application test exists yet, so none is claimed.

## 2026-11-11 — Import/API integration, first red checkpoint

Implemented API and synthetic seed/fixture generator. Strict mypy initially found six generic model errors; added a typed shared portfolio model base and reran successfully (15 files). The first actual PostgreSQL integration suite returned **2 failed, 15 passed in 14.40s**. D005: immutable billing snapshot header was flushed before its final total was calculated. Database guard rejected the later update. HTTP teardown permitted an apparent success before rollback, discovered by subsequent CSV export 404. Saving failing regression tests and the observed result before correction. This is an intentionally incomplete checkpoint, not an accepted phase.

## 2026-11-11 — Immutable preview correction, green verification

Corrected D005 by calculating preview lines/total before header insertion. Applied function-scoped FastAPI transaction dependencies so commit failures cannot be reported as successful responses. Refined cutoff design: financial reads serialize with source publication, completed imports bound source eligibility, and exception state reconstructs from audit records at the cutoff. Rerun: **17 passed, 1 upstream deprecation warning in 13.70s**, strict mypy passes 15 files, Ruff passes. This is the observed red-to-green transition from checkpoint `5f191c5`.

Frontend development began with React/TypeScript, live API contract, all six operational views, source/report dialogs and CSV download. npm install completed: 72 packages, zero reported vulnerabilities. First build was invoked from repository root and failed ENOENT; corrected invocation uses frontend directory. Build/browser verification not yet claimed.

## 2026-11-11 — Historical publication refinement

A first cutoff test without pre-existing leases passed but did not exercise ledger effects; strengthened the case with previously published leases and a later financial import. Targeted regression then failed: expected two missing charges before later batch publication, observed one (1 failed in 0.56s). Found the ledger query joined ImportJob but lacked its completed-at predicate; lease/raw queries already had it. Corrected ledger predicate; rerun pending. This distinguishes a weak initial test from the later reproducer rather than claiming the first test proved the invariant.

Frontend `npm run build` from frontend completed: strict TypeScript and Vite succeeded, 1,580 modules; 265.29 kB JS (80.80 kB gzip), 20.69 kB CSS, build 11.68s. Live API seeded, local Vite/API/worker started. Chrome journey/mobile tests written and launched. A repeated root-directory npm invocation failed ENOENT; commands will be centralized in Makefile to prevent this operator error.

### Browser correction sequence

After the origin fix, mobile viewport test passed. Journey first exposed stale feedback timing: success notice was rendered before refreshed import history, so the old batch could be inspected (1 failed / 1 passed, 11.5s). Moved notice emission after data reload. Next run advanced through replay/source/reconciliation/review to billing, where the test incorrectly assumed decimal-point formatting; browser's en-ZA uses comma. Corrected only the display assertion to accept locale separators, preserving exact Decimal API and CSV assertions (1 failed / 1 passed, 13.4s). Added Escape handling, focus containment/restoration for dialogs, removed externally fetched fonts and formatted frontend for reviewability. Running next verification before acceptance.

The 10k acceptance run has completed its first import: worker observed **100,429 ms** processing time. Replay is still running; no final benchmark result yet. This is a baseline, not a claimed performance improvement.

## 2026-11-11 07:25:42 UTC — Acceptance and first load baseline

Full isolated acceptance completed successfully: both provider HTTP imports, source-backed leases/ledger, reconciliation, audit review, idempotent preview and CSV, then deterministic 10k financial events and replay. Imported 10,002 accepted source rows (two leases included), quarantined two; replay produced 10,002 duplicates and two quarantines, zero accepted. Exactly 10,000 ledger entries remained, total ZAR 18,750,000.00. Initial import 100.590s, replay 80.810s, full run 182.079s. Checked in sanitized machine output; no credential traces included. This is an intentionally honest performance baseline, with no before/after improvement asserted.

Browser rerun then revealed navigation accessible-name instability after accumulated exception counts. Added stable aria-label, keeping visible counts. Mobile continued to pass. Journey remains unaccepted until rerun passes.

## 2026-11-11 — Browser milestone green, container build

Chrome reviewer journey and mobile viewport now **2 passed in 7.3s**. The last test correction selected Ledger explicitly after reload; backend persistence was intact and only local UI mode reset. Expanded worker/error/revision suite **24 passed in 8.03s**, 85% coverage (larger seed-code denominator). Container builds succeeded for all three app images. Recording milestone before release/container persistence work. No hosted CI or public deployment result is inferred from these local checks.

## 2026-11-11 — Final database-boundary audit

Added direct-DB tests beyond the already passing API authorization/source service tests. Both failed (2 failed in 0.74s): pricing FK linked only global pricing ID, and ledger's type-inclusive unique constraint permitted a second posting of another kind with same event/revision. These were blocked by current service logic but not database boundary. Add migration `b002` with composite pricing scope and partial uniqueness across non-reversal types; keep reversal coexistence. This is explicit schema evolution after initial applied migrations, not rewriting history. Also adding positive revision and row/job validity checks.

## 2026-11-11 — Database hardening green and release checkpoint

Added b002 as a new migration, enforcing pricing portfolio ownership and type-independent non-reversal event identity. Both failing direct-DB tests now pass; complete suite **26 passed / one upstream warning in 9.23s**, 85% coverage. Strict mypy passes. Added durable recovery fixture to seed (real injected rollback then second attempt), CI and operational documentation. Container runtime verification next; no cloud resources created. Removed accidentally tracked tsconfig.tsbuildinfo and ignored generated build-state files. No claimed bulk-performance improvement; repeat acceptance planned because schema invariants changed.

## 2026-11-11 — Full container runtime accepted, persistence check pending

Stopped only the three development processes created for this task and replaced them with container API/worker/Nginx. Compose health checks passed. Existing populated DB upgraded to b002; Alembic metadata comparison found no new operations. Recovery.csv shows real rolled-back first attempt then second-attempt completion with 7 duplicates and no new ledger effects. Chrome reviewer journey/mobile through built Nginx frontend **2 passed in 7.5s**. `make check` passes every static/build stage. Waiting for repeated 10k acceptance before intentionally cycling the DB/container stack; interrupting its active transaction would invalidate benchmark evidence.

## 2026-11-11 07:36:39 UTC — Hardened acceptance repeat passed

Repeated isolated journey/10k/replay on committed backend/schema d741c76, with documentation dirty state disclosed in machine output. Same exact counts and total: 10,002 accepted rows then 10,002 duplicates, two quarantines each, 10,000 postings and ZAR 18,750,000.00. Initial 100.555s, replay 63.949s, full 165.238s. Compared with 100.590s/80.810s initial baseline; no controlled optimization was performed, so recorded as repeat variability rather than causal performance improvement. Saved sanitized JSON. Captured authenticated synthetic desktop/mobile overview evidence; local trace artifacts remain untracked. Rotating generated demo password and revoking debug sessions before final persistence check; no password value is part of documentation or commits.

## 2026-11-11 — Named-volume persistence proved

Executed full Compose down/up after isolated acceptance finished. Compared exact business-record IDs and ledger total to captured pre-stop state: passed. Counts: 9 ledger, 3 leases, 4 previews/8 lines, 31 audit, 52 exception, 9 jobs; total ZAR 19,500.00. Captured sanitized comparison JSON and reusable read-only persistence smoke script. Public auth/schema readiness healthy; final browser run verifies the rotated generated local credential and post-restart operation. Repeated reviewer actions account for accumulated exception/job/preview counts; no reset or invented demo metric is used.

## 2026-11-11 — Final verified local release

Post-stop/start Chrome journey/mobile **2 passed in 6.9s**, including login using rotated generated demo credential. Final static/build checks pass; git whitespace check clean and tracked current-credential scan passes. Existing public GitHub repository metadata verified read-only, with no push/hosted Actions/public API deployment claim. Final docs include fresh-clone start/login process, synthetic non-affiliation, architecture/mappings/schema/decisions, security/tradeoffs/operations/deployment blockers, actual performance and recovery evidence, reviewer narration and truthful application description. Added root AGENTS.md to preserve the owner's continuous-documentation acceptance requirement for future contributors. Saving final evidence as a separate increment; implementation remains a local synthetic demonstration with enumerated public-hosting gaps.

## 2026-11-11 12:26:34 UTC — Iteration 005 reconnaissance

Starting SHA `3a605a0b130a9ece50b9308cef198573b85383b8`, branch `codex/portfolio-ledger-build`, 14 dirty tracked files (318 insertions/100 deletions). Preserved all pre-existing changes; created `codex/portfolio-ledger-release-ui-v2`. Read supplied iteration brief, AGENTS, README, domain rules, journal, security, deployment, validation and tradeoffs; inspected CI and migration history. Local origin/main comparison contains the same dirty files; no additional local hardening branch. Existing changes largely formatting plus validation/money corrections, not the requested registry/production profile.

Objective: full neutral design system and real release boundaries, with actual local verification and no public writable deployment. Baseline `make check`: Ruff lint passed; formatter failed on 11 existing dirty files. Docker initially unavailable; top-level app launch failed kLSNoExecutableErr, nested Docker Desktop application launch succeeded. PostgreSQL and browser baseline pending. Git branch creation initially denied by filesystem policy; approved retry succeeded. No secrets printed.

## 2026-11-11 12:34:20 UTC — Baseline and release regressions

Approved local Docker startup succeeded. Initial unprivileged PostgreSQL run: 7 passed / 19 setup errors (connection access/infrastructure); approved rerun: 26 passed, one upstream warning, 13.36s, 85% coverage. Baseline Chrome: 2 passed in 9.6s. Captured 11 credential-free screenshots under docs/evidence/ui/before (all six views, ledger, evidence modal, login, tablet/mobile overview). First screenshot script invocation used the wrong working-directory prefix and failed; corrected invocation succeeded.

New regression checkpoint before implementation: 5 failed in 1.39s. Arbitrary source upload actually returned 202; readiness helper absent; early 400 lacked security headers; production configuration accepted unsafe defaults; public reviewer configuration absent. Tests now drive the security increment. Error output can contain settings values; raw logs are excluded from Git and only aggregate results recorded here.

Implementation in progress: full neutral token stylesheet, extracted Badge/Empty/Table/Pager/Panel; additive b003 registry with historical identities disabled pending explicit operator review; registry checks at upload, replay and processing; dynamic Alembic readiness; strict production config; bounded streamed request parser; explicit synthetic seed; dedicated scoped public reviewer; session/rate cleanup. No migration or final green claim yet.

## 2026-11-11 12:40:07 UTC — Registry/security green and complete container rebuild

First new security rerun: 4 passed / 1 failed (2.83s), early error response still bypassed header assignment after an overly narrow text edit. Corrected response flow; full suite then 31 passed in 18.86s. Removed unused frontend imports found by TypeScript; strict check/build/style guard now pass. Expanded registry and privilege suite: 35 passed, one warning, 56.94s (concurrent container build; no performance comparison claimed). Tests cover actual same-feed alias rejection without posting inflation, enabled independent source accounts, disabled-source replay, cross-portfolio registry, global public write lock, invalid synthetic grants, streamed oversize rejection, hostile Host and non-owner runtime-role denial of trigger disable/truncate/evidence updates/deletes/registry writes.

Docker Compose rebuild succeeded; explicit release service migrated existing database to b003 and seeded only the explicit synthetic namespace. API healthy, worker/web running with non-root IDs and restricted capabilities/read-only filesystems. Public UI/functional/axe audit and isolated backup restore currently running. Current remote inspected read-only: main 21275fa; original build branch 3a605a0; PR #1 merged. No unpushed hardening branch found.

## 2026-11-11 12:47:11 UTC — Visual review, accessibility, backup and acceptance

Chrome expanded suite: 6 passed in 56.5s. Every operational view at 320/390/430/768/1024/1440, controls >=40px, table-region scrolling, search/empty, modal focus/Escape/restoration, session persistence and private read-only evidence/CSV verified. Axe WCAG A/AA/2.1 AA found no violations on login and six operational screens. Viewed actual before desktop overview/login and after login/overview/integrations/leases/evidence modal/reconciliation/billing/audit/tablet/mobile screenshots; neutral palette and rounded controls consistent. Found cramped metric-note spacing; added gap and softened uppercase metadata. Public reviewer browser check remains pending.

Dependency scans: npm reports zero vulnerabilities; unsuppressed pip-audit reports no known vulnerabilities, excluding only unpublished local portfolio-ledger distribution (not on PyPI). No OS-image scan or future-security guarantee claimed.

First isolated backup restore failed on existing default schema in the new target. Corrected restore flags restricted to disposable target. Repeat passed: 13 business table count/content hashes match, source unchanged, restored ledger trigger enforced, ledger ZAR 19,500.00. Private dump deleted; restore database removed. Evidence backup-restore.json.

Full b003 isolated 10k acceptance passed at 12:45:16 UTC: 10,002 accepted / 2 quarantined; replay 10,002 duplicates / 2 quarantined / 0 accepted; 10,000 postings / ZAR 18,750,000.00. Initial 190.983s, replay 82.724s, full 275.891s. Dirty base 3a605a0, concurrent verification; slower than prior run, no causal throughput assertion. Saved sanitized acceptance-release-ui.json.

Expanded production config, historical b002-to-b003 migration and separate runtime financial journey: 39 passed, one upstream warning, 34.13s, 85% coverage. Full journey authenticates/API imports through API role, worker posts through worker role, reconciliation/preview/CSV pass and production readiness accepts runtime role while rejecting owner. Added bounded session counts/expiry and verified cleanup. Standalone production Compose is configuration preparation; hosted infrastructure unverified.

## 2026-11-11 12:53:22 UTC — Final boundary checks and public browser correction

40 PostgreSQL tests passed in 18.34s, 85% coverage, one upstream warning; added continuous synthetic-scope checks after a public session is created. Identity response now exposes effective read-only state so global public mode is reflected in controls. Static type checker found a bool/SQL expression union in scope filtering; replaced Python true with SQL true(), check passed. Alembic check: no new upgrade operations detected. Actual runtime IDs: API/worker UID 10001, Nginx UID 101. Nginx local syntax test passed. Production Compose rejects missing required variables and renders with synthetic TLS/host/proxy placeholders without provisioning. Benchmark hardware read afterward: Apple M5, 16 GiB RAM; first restricted hardware query denied, approved query succeeded.

Public Chrome case first timed out because Escape fired before asynchronous report opening. Second run reached direct business mutation-denial checks and CSV but helper incorrectly expected Close to retain focus after Download; corrected helper to focus Close then Escape and assert disappearance. These are test synchronization/expectation defects, not relaxed business assertions. Business-ID/total comparison remained unchanged through attempts (9 ledger, 3 leases, 8 previews/15 lines, 48 audits, 119 exceptions, 12 jobs; ZAR 19,500.00). Final public rerun pending.

## 2026-11-11 12:54:28 UTC — Public reviewer accepted

Third public-test rerun reached Audit and found a test-only heading typo (omitted ampersand in existing Execution & audit timeline). Corrected locator without changing product copy/assertions. Final public Chrome case: 1 passed in 4.2s (2.5s case). Password-free reviewer inspected reports, ledger source evidence, exceptions, preview CSV and audit; direct upload/replay/reconciliation/review/preview calls all 403. Business-ID/ledger comparison unchanged; sanitized public-review.json and credential-free public-review-audit screenshot saved. Production Nginx configuration tested inside actual non-root image: syntax successful (entrypoint read-only-config notice expected). Final candidate credential scan passed. Saving implementation increment before restart/final evidence increment.

## 2026-11-11 12:58:27 UTC — Restart accepted; final ownership regression

Implementation increment committed as 7ed81c6. Complete Compose down/up (no volume removal) passed exact-ID/ledger comparison: 9 postings, 3 leases, 8 previews/15 lines, 48 audits, 119 exceptions, 12 jobs; ZAR 19,500.00. Sanitized persistence-release.json saved.

Final privilege review identified schema ownership as a second DDL bypass path despite non-ownership of individual tables. Added reproducer: 1 failed in 0.50s (expected owner-rejection exception did not occur). Role setup and production readiness now check database/schema ownership and membership as well as table ownership/role flags. Existing separate-role financial journey now also asserts readiness becomes 503 if runtime role is temporarily assigned schema ownership, then restores ownership in test cleanup. Configuration repr/errors now redact secret fields and production rejects socket/unnamed DB identities. Full suite/static rerun pending. No finance/schema/worker logic changed in this correction.

## 2026-11-11 12:59:20 UTC — Ownership correction green

Full PostgreSQL suite: 41 passed / 35.88s / 85% / one upstream warning. Schema-owner reproducer now passes, ordinary separate-runtime financial journey stays green, production readiness rejects schema ownership. All static/type/build/style checks pass. No finance logic, source identity, worker processing or Alembic schema changed after the accepted 10k run; no benchmark rerun asserted. Final images rebuilding before browser/capture verification.

## 2026-11-11 13:02:58 UTC — Final visual/accessibility correction

Public case rerun against final rebuilt backend: 1 passed in 5.5s; stricter screenshot waits now require the real audit rows loaded and scroll to page top. Manual review had caught an earlier public capture before audit data finished loading; replacement is required, not claimed accepted.

Private final browser rerun: 5 passed / 1 failed, 19.0s. Axe caught Integrations navigation at intermediate transition colors (contrast 1.12/2.23 while text/background swapped). Removed only navigation color transitions so selected background/text switch together; unchanged axe assertions and full journey rerunning. This is a genuine transient style defect, not a reason to disable contrast checking or introduce test sleeps.

## 2026-11-11 13:07:13 UTC — Final local acceptance and reviewed captures

D023 corrected: full private Chrome suite 6 passed in 19.2s; unchanged axe contrast checks pass login and all six operational views, responsive 36 combinations and all finance assertions retained. Final public Chrome 1 passed in 4.2s; exact business-ID/ledger comparison unchanged (9 postings, 3 leases, 10 previews/19 lines, 58 audits, 173 exceptions, 14 jobs, ZAR 19,500.00). Private runs legitimately added review/import/preview history between public/restart measurement boundaries; no data reset. Returned stack to private mode.

Final screenshot helper initially captured images but failed logout because standalone browser request context lacked a base URL. Added explicit loopback base URL and finally-close; complete rerun exited 0 (Captured after synthetic UI screenshots), including session revocation. Refreshed all six screens plus login, ledger, source modal, tablet/mobile. Actually viewed final overview/mobile/tablet/login/integrations/leases/modal/reconciliation/billing and public Audit; all neutral/rounded/legible, no clipped document or credentials. Public Audit now contains actual loaded rows and sidebar starts at top; screenshots accepted.

Final static/type/build/style and credential/artifact checks passed at this checkpoint (latest final command completion recorded before commit). No new backend business/schema/worker change after accepted 10k run. Local backup/restore and full named-volume restart have genuine evidence. Hosted candidate CI, HTTPS deployment, hosted TLS DB/backup/alerting remain unverified; public release NO-GO. Implementation and local acceptance complete; branch publication remains conditional on owner authorization per supplied phase 5.

## 2026-11-11 13:11:01 UTC — Browser-facing readiness corrected and final candidate saved

Final endpoint audit found real `/ready` through Nginx returned 400 despite direct API health: that location omitted browser Host, so strict TrustedHost rejected internal upstream hostname. Kept host enforcement and forwarded original Host/protocol in both local/production readiness locations. Added actual readiness-dialog assertion to original journey and same-origin readiness assertion to public test. Production Nginx syntax passes in actual non-root image; curl via frontend now 200 with b003. Private full suite **6 passed / 33.1s**, public **1 passed / 9.9s**, including all existing financial/axe assertions. Public exact business-ID/ledger comparison passed again; private reviewer actions between checkpoints account for 11 previews/21 lines, 63 audits, 203 exceptions and 15 jobs (ledger still 9 / ZAR 19,500.00).

Returned private mode. Immediate curl during API recreation briefly returned 502 before health startup; subsequent explicit readiness check returned ready/b003 and auth options public_review_enabled=false. No steady-state failure or uptime claim inferred. Final static/type/build/style and credential/artifact scans passed; git diff whitespace clean. All current implementation/evidence files are being saved as a second meaningful increment. No push, new PR, candidate hosted CI or cloud deployment performed; those remain conditional release gates.

## 2026-11-11 13:15:31 UTC — Authorized publication and real hosted audit failure

Owner explicitly authorized pushing and opening draft PR. Pushed 1eef601 on release branch. GitHub connector PR creation returned 403 (integration permission); authenticated gh fallback successfully opened draft PR #2: https://github.com/keenosmith-del/portfolio-ledger/pull/2. Initial hosted push run 43027005906 actually failed at pip-audit: runner venv bundled pip 25.0.1, scanner reported 12 findings in that single tooling package (including duplicated advisory aliases). No backend/browser hosted success inferred. PR-triggered same-SHA run initially in progress.

Correction: upgrade pip>=26.2 before dependency installation in CI/local setup/container build, retaining unsuppressed audit. Add per-branch workflow concurrency cancellation so push/PR events do not wastefully run duplicate full suites. This is tooling/release configuration, no finance/domain/schema behavior change. Hosted rerun and runtime image audit pending.

## 2026-11-11 13:20:43 UTC — Hosted tooling correction verified; runtime audit

Committed/pushed 65fdea6 with pip upgrade and branch concurrency. Corrected PR run https://github.com/keenosmith-del/portfolio-ledger/actions/runs/43027530061 has actually passed static/type/build, unsuppressed Python/npm audits, PostgreSQL tests, migration and seed; 10k acceptance running at this entry. Duplicate push run cancelled by explicit concurrency, not reported as a failed financial check.

Rebuilt local release/API/worker images and reached healthy startup. Actual runtime pip is 26.3 (development venv pip 26.2.1). Audited exact installed runtime Python package inventory excluding unpublished project code: no known vulnerabilities in 33 packages, no advisory suppressions. Scanner recommends distribution hashes; OS packages remain unscanned. Saved runtime-dependency-audit.json. First evidence metadata lookup used system Python lacking pip-audit metadata; corrected to project venv. No dependency-lock/reproducible-build claim.

## 2026-11-11 13:26:55 UTC — Hosted code candidate accepted

Inspected successful PR run https://github.com/keenosmith-del/portfolio-ledger/actions/runs/43027530061 for head 65fdea6f4a9f0df01fa2cd65dd50706b32b91012, tested merge ref 2a22123. Actual results: 41 backend tests / 22.74s / one warning; private Chrome 6 / 24.4s; public Chrome 1 / 3.4s. Static/type/build/style, unsuppressed Python/npm audits, migrations, seed and 10k acceptance passed. Hosted Linux x86_64 / Python 3.12.16 clean-checkout benchmark: import 87.758s, replay 55.098s, full 143.709s; exact 10,002 accepted then 10,002 duplicates, two quarantines each, 10,000 postings / ZAR 18,750,000.00. Different platform from local; no controlled speedup claim.

Sanitized hosted-ci.json, acceptance-hosted.json and runtime-dependency-audit.json saved in evidence commit 1554cdc. A quoting error interrupted the accompanying narrative update; corrected here, no application code affected. Owner authorized publication and draft PR #2. This is evidence/documentation only after the accepted code candidate. Whitespace and private-credential scans passed; latest PR Actions remains the live merge gate. Public hosting still NO-GO pending operator HTTPS/TLS DB/secrets/hosted restore/alerts. Owner's next action is PR/visual review.

## 2026-11-11 17:18:05 UTC — Railway/Neon deployment reconnaissance

Starting state clean main 22ce9b4, merged PR #2. Read README/domain rules/current journal, deployment/security contract, production Compose, Dockerfiles, role setup and worker. Created codex/railway-neon-deployment. Provider CLIs absent, provider credential environment variable names absent; Neon config contained only anonymous_id. Discovered available but unconnected Railway/Neon integrations; requested connection. Browser sign-in initially required, owner subsequently confirmed signed-in Chrome tabs.

Observed Neon project portfolioledger (twilight-shadow-25760482), production branch br-bitter-truth-bdkvicny, Free plan, PostgreSQL 18, Ohio region, six-hour history retention. Owner connection panel was open; hid password and retained no secret in repository/evidence. Railway existing project amiable-imagination (34e13a89-756c-4a34-8e29-845dedeaeb11), one unexposed portfolio-ledger service, trial banner 30 days or $5 remaining. Failed deployment 169e2872 used Railpack at repository root and never deployed. Build diagnostics being inspected. No resources/plans purchased or destructive operations performed.

Objective: adapt existing containers into separate web/api/worker Railway services with Neon direct verified TLS; one-off owner release, distinct runtime roles, public read-only review and real hosted verification. Platform docs reviewed: Railway config-as-code/private networking/healthcheck host/PORT, Neon SQL roles and verify-full TLS. Plan: service-specific Docker configs, dual-stack API binding, exact DNS-resolved web proxy trust, Nginx same-origin template with runtime upstream resolution, isolated owner release and non-mutating deployment checks. Hosted release remains NO-GO pending actual connectivity, secret setup, roles, browser and operational checks.

## 2026-11-11 17:32:17 UTC — Deployment configuration implemented and local checks accepted

Confirmed Railway failure: Railpack 0.43.0 could not determine the application at repository root (deployment 169e2872, main 22ce9b4); no runtime started. Added per-service Dockerfile configurations, unprivileged same-origin Railway Nginx template, exact private DNS proxy trust with dual-stack API binding, trusted CA bundle configuration, explicit owner-only release and read-only Neon connection verification. No financial/schema/worker processing changes.

Actual checks on dirty codex/railway-neon-deployment based on 22ce9b4: make check passed; make test 44 passed / 16.78s / one warning / 83% coverage. Both deployment Docker images built successfully. Backend UID 10001 and readable CA bundle verified. Frontend UID 101, actual generated Nginx configuration syntax passed, canonical Host HTTP 200, unknown Host closed with Nginx 444 (curl exit 52 / HTTP 000 expected). Temporary local container removed. Initial restricted Docker commands were denied access to socket; authorized execution succeeded. No hosted verification inferred. Existing accepted 10k evidence preserved; no load test executed against Neon.

Owner authorized storing project-restricted Neon key and scoped Railway CLI connection. Railway first OAuth callback expired; repeated scoped consent succeeded and CLI linked only existing project 34e13a89 / production / failed service. Neon profile --mint requires temporary organization-wide OAuth scopes even when final key is project-restricted: automatic review rejected browser navigation. Stopped that flow; prepared Console project-scoped key form selecting portfolioledger and requested owner to save key privately. No broad Neon authorization or paid plan approved. API/worker owner secrets remain unconfigured, cloud release remains NO-GO.

## 2026-11-11 17:37:00 UTC — Current Railway infrastructure format corrected

GraphQL rejected builder DOCKERFILE (not in its older Builder enum) before mutations; subsequent request renamed project portfolioledger but serviceUpdate returned Not Authorized. Standalone serviceInstanceUpdate rejected legacy TOML opt-in: current platform requires Infrastructure as Code. Official docs confirm new-service restriction since August 28 and legacy cutoff December 1. Imported existing project with variables unmanaged, installed official railway SDK 3.16.0 only under .railway and replaced unpublished TOML files with .railway/railway.ts. Native Console rename succeeded for existing failed service to web; CLI private endpoint update verified web.railway.internal, dual-stack, ACTIVE, no running private IP yet.

Actual config plan succeeded: safe web source/build/start/readiness/restart updates plus new api and worker; zero destroy, no variables read/written. Provider settings preparation only; no cloud runtime success claimed. Owner asked where to store project-scoped Neon key; supplied exact private TextEdit/file steps.

## 2026-11-11 17:41:55 UTC — Infrastructure applied and scoped Neon credential stored

Committed/pushed a9eeaa7, Actions 43069924214 started. Railway current IaC apply succeeded: web updated, private api (1221c1fe) and worker (ef3a0507) created, no destructive changes. Only web generated HTTPS domain web-production-6a3f45e7.up.railway.app on port 8080. Verified private api/worker DNS endpoints ACTIVE dual-stack with no public domains. Applied non-secret production/read-only/origin/Host/proxy configuration with skip-deploys. First cloud backend Docker builds reached healthcheck; initial API health 400 and worker crashed because build began before production/database variables existed. Not a completed runtime rollout.

Owner saved project-scoped Neon API key via TextEdit to its iCloud folder and asked for help locating it. Used that exact file privately, CLI profile creation succeeded, removed temporary plaintext source and empty /tmp key file, closed credential document. No broad Neon OAuth used. Direct verified-TLS connection retrieval now running with project-scoped profile and output captured privately.

Prepared HTTPS-only hosted browser configuration, cookie/CSRF/Host/portfolio checks and small availability workflow (disabled until public URL repository variable set and workflow reaches default branch). Static rerun initially found formatter-only issue in monitor; corrected, make check passed. No hosted browser or monitoring success inferred.

## 2026-11-11 17:43:57 UTC — Real CI/environment and Neon TLS findings

Actions 43069924214 failed: 43 tests passed, new Settings test failed because workflow PUBLIC_REVIEW_ENABLED=true was inherited while its constructed production settings omitted PUBLIC_DEMO_READ_ONLY. Added both explicit true values in test fixture, preserving fail-closed rule. Exact CI-environment targeted rerun 3 passed / 0.05s / one warning.

Direct Neon preflight found empty public schema (0 tables), owner CREATEROLE/CREATEDB both true. pg_stat_ssl returned false/null despite sslmode=verify-full. Investigated actual client: libpq ssl_in_use true. Psycopg exposes ssl_in_use but not ssl_attribute_names (attempt raised AttributeError, no TLS version fabricated). PostgreSQL libpq docs identify client SSL state as the direct signal; Neon proxy is a separate hop from backend statistics. Corrected operator inspector to require both actual client TLS and live sslmode=verify-full, retaining server stats separately. Added rejection test for plaintext client and weak mode; full checks/tests running before owner release. No certificate verification disabled.

## 2026-11-11 17:44:46 UTC — Corrected local gate accepted; owner release started

make check passed. Full PostgreSQL regression 45 passed / 20.07s / one warning / 83% coverage on dirty deployment branch after a9eeaa7. Actual Neon client TLS active + live verify-full preflight passed. Started explicit one-off app.operations.release with private owner environment after confirming empty target schema. Output captured privately, exception reporting sanitized; owner credentials never set on ordinary services. Outcome pending, no success inferred.

## 2026-11-11 17:49:33 UTC — Neon release and runtime boundaries verified

Explicit owner release completed successfully: Alembic b003, bundled synthetic seed, SQL-created independent API/worker roles and actual-client TLS. Both runtime connections passed inspector: client TLS true, verify-full, direct non-pooled connection, current b003, no privileged flags/memberships or database/schema/table ownership. Sanitized neon-runtime-verification.json saved. Only respective runtime DATABASE_URL values were sent to Railway via stdin, skip-deploys; owner secrets never attached. Worker startup log before runtime DSNs confirmed production safeguard rejected missing private verified-TLS role.

Created draft PR #3. Push run 43071119108 cancelled normally by PR concurrency; replacement 43071397070 passed tests/static/audits and reached isolated financial acceptance. Added hosted restore script: only synthetic portfolios, new uniquely named database, PostgreSQL 18 pg_dump/pg_restore, client verify-full, exact business table hashes/IDs/total and source-unchanged comparison, private dump removed, no database deletion. Formatter/import/check-argument issues corrected before make check passed. Hosted drill started; result pending.

## 2026-11-11 17:55:59 UTC — CI green; real cloud bootstrap and restore defects corrected

Corrected PR CI 43071397070 succeeded for db1b599, including 45 PostgreSQL tests, isolated 10k financial acceptance, private/public browser and audits/static checks. Redeployed all three services with private runtime DSNs. Worker reached SUCCESS; API/web remained DEPLOYING. Public HTTPS request reached Railway edge but returned application-not-found 404 while deployment was not ready (no success inferred). API logs showed web DNS absent; web health logs showed api DNS absent. This is a real startup cycle because web's API readiness healthcheck blocks publication of web DNS needed for API exact proxy trust. Changed only web startup healthcheck to static homepage; public /ready still checks API/database. Safe IaC plan/apply succeeded, no wildcard or broad proxy trust.

Hosted restore failed; read-only pg_dump schema preflight passed with client 18.6 and readable trusted CA bundle. Verified isolated restore DB public tables=0. Retried only that empty isolated DB to obtain sanitized actual error: public schema already exists. Corrected archive TOC to omit exactly one public-schema CREATE entry; no DROP/clean/production overwrite. Retry in same verified-empty isolated database running. Added HSTS to Railway Nginx and assertion to hosted security case; static/type/build/style check passed before upcoming publication.

## 2026-11-11 17:59:35 UTC — Hosted restore verified; web bootstrap accepted

Hosted restore retry passed exact hashes/IDs across 14 business tables and ledger total; source unchanged, temporary private dump removed. Retained isolated database portfolioledger_restore_202611111749116dacb6 for owner review; no database dropped or source reset. Sanitized neon-restore-verification.json saved.

Web static startup health succeeded: actual HTTPS homepage HTTP 200. /ready still returned 502 while private API not ready. Railway restart API reported deployment not restartable, so retried redeploy (not security relaxation). CLI SSH diagnostic unavailable because account has no registered SSH keys; no extra SSH credential created. Railway DNS logs subsequently verified web.railway.internal NOERROR A/AAAA (earlier NXDOMAIN), demonstrating corrected startup cycle. API startup/recovery validation pending.

## 2026-11-11 18:01:54 UTC — True dual-family listener correction

After web succeeded and private DNS logs showed A/AAAA, API launched Uvicorn on [::]:8000 but did not receive Railway health requests. Installed server uses asyncio create_server(host=::); actual loopback reproducer reported IPV6_V6ONLY=1 and IPv4 ConnectionRefusedError. Replaced implicit listener with explicit IPv6 socket IPV6_V6ONLY=0 passed to Uvicorn Server, preserving precise proxy/origin/Host validation. Added real IPv4 + IPv6 connection regression and exact IPv4-mapped peer address variants for trusted proxy IPs (never a CIDR/wildcard). Verification running. Previous accepted CI remains db1b599; 7a87031 published restore/startup/HSTS increment before this finding.

## 2026-11-11 18:03:21 UTC — Listener regression accepted; mapped-IP assertion corrected

Full local PostgreSQL run passed 46 tests / 22.17s / one warning / 82% coverage after dual-family socket change. Added mapped IPv4 trust variants afterward and static checks passed, but concurrent publication 3821dda completed before targeted test returned one failure: Python 3.14 renders mapped addresses dotted whereas expected literal used hexadecimal. Runtime trust parses addresses correctly; changed assertion to compare IP address objects across Python versions. Exact CI-environment targeted rerun now 5 passed / 0.05s / one warning. This failed test/publication order is retained; no false passing claim for that intermediate assertion.

Hosted restore completed before staging the worker recovery drill. New synthetic duplicate replay is staged with a deliberately injected processing lease; actual Railway worker restart/recovery and unchanged ledger hash will be verified. This injection is operator-controlled test evidence, not an invented real outage. No public mutation route enabled.

## 2026-11-11 18:05:12 UTC — Mapped-address CI failure and precise recovery evidence

CI 43073887308 for 3821dda failed only mapped-address string assertion (45 passed/1 failed, 21.21s). Contrary to initial Python-version inference, CI Python 3.12 also renders mapped addresses dotted. The corrected address-object assertion passed locally (5/0.05s); make check passed. Publishing that correction now, without changing runtime behavior.

Worker lease recovery itself passed on the existing running service: injected processing lease expired, attempt two partially_completed with seven duplicates/zero accepted and unchanged ledger hash. CLI restart attempt returned deployment not restartable because latest deployment was queued, so this does NOT prove a completed worker restart. Corrected uncommitted evidence restart flag to false immediately; real restart remains a separate outstanding gate. No new SSH key/access created.
