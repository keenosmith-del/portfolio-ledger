# Defect and obstacle log

| ID | Observed | Correction | Verification |
|---|---|---|---|
| D001 | Dependency download DNS denied in restricted execution | Approved network installation | pip editable install completed |
| D002 | Docker engine stopped; short app name launch failed | Launch explicit Docker.app with approval | PostgreSQL container started |
| D003 | Compose db startup blocked by required app password interpolation | Private generated `.env`, mode 0600 | `docker compose up -d db` succeeded |

Application defects will be appended with the failing test/command and passing rerun. Infrastructure obstacles are distinguished from application test failures; none of these are represented as failed invariant tests.

| D004 | Strict typing found six generic pagination/scoping attribute errors after Ruff rewrote getattr | Introduced typed PortfolioEntity base | mypy passed 15 files |
| D005 | First PostgreSQL suite: immutable billing header was inserted at zero then updated; concurrent preview failed and HTTP export returned 404 | Correction pending: compute before insertion, enforce transaction completion before HTTP success | Red run: 2 failed / 15 passed, 14.40s |

| D005 fixed | Billing header immutability / HTTP success before commit | Compute line eligibility and total before INSERT; FastAPI dependencies use function scope so commit completes before response | Full suite: 17 passed / 1 upstream warning, 13.70s |
| D006 | First frontend build invoked at repository root (no package.json) | Run in frontend directory; Makefile will encode correct directory | Correct build rerun pending |

| D007 | Added cutoff regression found already-created ledger rows included before their batch completion: expected two missing charges, observed one | Apply ImportJob.completed_at cutoff predicate to ledger query as well as lease/raw queries | First targeted run: 1 failed in 0.56s; passing rerun pending |

| D007 fixed | Missing ledger publication cutoff | Require completed-at predicate on ledger query | Expanded suite 22 passed, 86% coverage, 8.04s |
| D008 | Both first Chrome tests failed login: localhost origin allowed but 127.0.0.1 frontend origin absent | Add explicit loopback origin; keep origin allowlist enforcement; resolve .env independent of working directory | Browser rerun pending |

| D009 | Browser rerun: mobile passed, journey inspected original batch too early after replay; notice appeared before table refresh (1 failed / 1 passed, 11.5s) | Emit success notice after refreshing persisted data; browser waits on new batch's completed state | Rerun pending |

| D010 | Browser journey reached persisted billing preview but test expected decimal point; Chrome en-ZA rendered `R 170,00` (mobile passed) | Test asserts equivalent locale decimal separators; monetary API/CSV assertions remain exact decimal strings | Browser rerun pending |

| D011 | Repeated browser runs accumulated exceptions, changing accessible nav button name to Reconciliation plus count; exact navigation locator timed out (mobile still passed) | Explicit stable aria-label on navigation controls; retain visible count | Rerun pending |

| D012 | Browser journey completed persisted preview/reload/audit, then expected a ledger event while viewing Leases after reload reset mode (1 failed / 1 passed, 13.7s) | Test explicitly selects Ledger for second portfolio instead of assuming pre-reload UI mode survives | Rerun pending |
