import { defineRailway, github, project, service } from "railway/iac";
// This repository manages only its own resources in the environment. Other
// repositories export their own partial name.
// See https://docs.railway.com/infrastructure-as-code#multi-repo-projects
export const partial = "candid";
export default defineRailway(() => {
  const candid = service("candid", {
    source: github("aditsawhney/candid", { branch: "main", checkSuites: false }),
    build: { buildEnvironment: "V3", builder: "RAILPACK" },
    start: "alembic upgrade head && uvicorn api.routes:app --host 0.0.0.0 --port $PORT",
    healthcheck: "/jobs",
    replicas: { "sfo": 1 },
  });

  return project("Candid", {
    variables: { managed: false },
    resources: [candid],
  });
});
