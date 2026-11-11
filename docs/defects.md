# Defect and obstacle log

| ID | Observed | Correction | Verification |
|---|---|---|---|
| D001 | Dependency download DNS denied in restricted execution | Approved network installation | pip editable install completed |
| D002 | Docker engine stopped; short app name launch failed | Launch explicit Docker.app with approval | PostgreSQL container started |
| D003 | Compose db startup blocked by required app password interpolation | Private generated `.env`, mode 0600 | `docker compose up -d db` succeeded |

Application defects will be appended with the failing test/command and passing rerun. Infrastructure obstacles are distinguished from application test failures; none of these are represented as failed invariant tests.
