# Railway deployment configuration

Run `npm ci --prefix .railway`, then `railway config plan` from repository root. Review the plan and use `railway config apply --yes` only for authorized changes with no destruction. Existing project: portfolioledger, production environment. Variables are deliberately unmanaged: use private provider variables, never owner credentials on runtime services.

The file manages web/api/worker from main, with source-directory watch paths. Apply promotion only after the deployment PR is merged and wait for successful GitHub checks. Only web may receive a generated public domain. Documentation-only changes do not rebuild runtime containers.

See [deployment guide](../docs/deployment.md) and [deployment evidence](../docs/iterations/007-railway-neon-deployment.md). No legacy railway.toml or Compose upload is used.
