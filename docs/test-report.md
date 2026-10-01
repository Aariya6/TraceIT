# TraceIT v5 test report

## Automated validation

`bash scripts/test_all.sh` runs the backend suite and JavaScript/HTML syntax checks.

Latest local result:

```text
11 passed
HTML structure check: PASS
JavaScript syntax check: PASS
Python compilation: PASS
```

The suite covers authentication, invalid login, bookmarks, auth-protected observations, triage, real Man Sagar record aggregation, clustering, recovery logic, neural anomaly scoring, live-data cataloguing and API health.

## Browser recording

`scripts/record_demo.py` records the landing page, research record, a real graph switch, sign-up flow and observation modal. It is designed to run against the deployed/static site with a reachable API.

The current build environment blocks Chromium navigation with an administrator policy, so no browser smoke test is falsely claimed as passed here.
