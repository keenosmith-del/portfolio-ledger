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
