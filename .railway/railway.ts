import { defineRailway, github, project, service, type DeployConfig } from "railway/iac";

// Secrets and environment-specific hostnames are supplied privately by the operator.
// No owner credentials or automatic migration hooks belong on runtime services.
export default defineRailway(() => {
  const deploy: DeployConfig = {
    sleepApplication: false,
    restartPolicyType: "ON_FAILURE",
    restartPolicyMaxRetries: 10,
  };
  const source = (rootDirectory: string) => github("keenosmith-del/portfolio-ledger", {
    branch: "codex/railway-neon-deployment",
    rootDirectory,
    checkSuites: true,
  });
  const build = { builder: "DOCKERFILE" as const, dockerfilePath: "Dockerfile" };
  const web = service("web", {
    source: source("/frontend"), build, replicas: { iad: 1 },
    start: "/bin/sh /opt/portfolioledger/start-railway.sh",
    healthcheck: "/", healthcheckTimeout: 300, deploy,
  });
  const api = service("api", {
    source: source("/backend"), build, replicas: { iad: 1 },
    start: "python -m app.operations.serve",
    healthcheck: "/ready", healthcheckTimeout: 300, deploy,
  });
  const worker = service("worker", {
    source: source("/backend"), build, replicas: { iad: 1 },
    start: "python -m app.workers.runner", deploy,
  });
  return project("portfolioledger", {
    variables: { managed: false },
    resources: [web, api, worker],
  });
});
