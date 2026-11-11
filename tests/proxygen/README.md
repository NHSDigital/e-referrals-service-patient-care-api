# Proxygen tests

Tests for an API instance deployed by Proxygen, using
[pytest-nhsd-apim](https://github.com/NHSDigital/pytest-nhsd-apim). They're separate from the
Apigee-era `tests/` suites (which use the `smoketest` marker and `tests/integration`) so the
existing pipelines don't pick them up.

| File | Needs a token | What it checks |
| --- | --- | --- |
| `test_proxygen_smoke.py` | No | `/_ping` works, undeclared paths 404, missing or invalid tokens get 401, `/_status` (when monitoring is on) |
| `test_proxygen_access.py` | Yes | pytest-nhsd-apim finds the generated proxy, and an NHS login P9 token passes Proxygen's auth |

Tests marked `apigee_token` are skipped when `APIGEE_ACCESS_TOKEN` isn't set, so the suite is
useful before you have Proxygen access to the token endpoint.

## Running locally

```bash
poetry install
# Optional: lets the token tests run. Needs the Proxygen CLI set up for this API.
export APIGEE_ACCESS_TOKEN=$(proxygen pytest-nhsd-apim get-token | jq -r .pytest_nhsd_apim_token)
make proxygen-test
```

The token lasts about an hour. Skipped tests and their reasons are listed at the end of the run.

### Settings

| Environment variable | Default | Notes |
| --- | --- | --- |
| `PROXYGEN_ENV` | `internal-dev` | Proxygen environment the instance is in |
| `PROXYGEN_API_NAME` | `e-referrals-service-patient-care-api-proxygen` | Proxygen API name |
| `PROXYGEN_BASE_PATH` | `e-referrals-service-patient-care-api-proxygen` | Instance base path, with `_` for `/`, as passed to `proxygen instance deploy` |
| `PROXYGEN_INCLUDE_PATHS` | `true` | Set `false` if the instance was deployed without `--include-paths`; skips `api_paths` tests |
| `APIGEE_ACCESS_TOKEN` | | From `proxygen pytest-nhsd-apim get-token`; enables `apigee_token` tests |
| `PROXYGEN_REQUIRE_APIGEE_TOKEN` | `false` | `true` fails the run when there's no token, rather than skipping |
| `STATUS_ENDPOINT_API_KEY` | | Key for `/_status`. Not needed in internal-dev, where the plugin fetches it with the token |

The pytest-nhsd-apim `--api-name` and `--proxy-name` flags aren't needed: `conftest.py`
derives them, using Proxygen's `<api name>--<env>--<base path>` proxy naming.

## In CI

`.github/workflows/proxygen-deploy-internal-dev.yml` runs the suite after deploying (the
`run-tests` input, on by default). It gets a token with the machine user's Proxygen
credentials; if that fails it logs a warning and the token tests are skipped. Once the
machine user can get tokens, set the `PROXYGEN_REQUIRE_APIGEE_TOKEN` variable to `true` on the
`proxygen-internal-dev` environment so a missing token fails the run. The JUnit report is
uploaded as the `proxygen-internal-dev-test-report` artifact.

## Strategy

1. **internal-dev, no target (now).** Prove Proxygen's layer: routing, auth rejection, and with
   a token, that a P9 token is accepted. The spec build grants a hidden product with the
   schemes the paths use (`x-nhsd-apim.access`) so pytest-nhsd-apim can subscribe a test app.
2. **internal-dev, with the adapter target.** Turn on `monitoring` and set `target` and
   `target-identity` in `specification/proxygen/internal-dev.yaml`. `/_status` tests then run,
   and `test_p9_patient_passes_proxygen_auth` should assert the backend's real responses. Port
   the scenarios in the migration plan's Testing section (unsupported VOT, invalid target ID,
   header spoofing, backend failure) here.
3. **Higher environments and prod.** Add an overlay per environment and run with
   `PROXYGEN_ENV` set. Prod differs:
   - Pass `--apigee-organization nhsd-prod`.
   - Use a pre-existing app instead of a generated one (`--apigee-app-id`).
   - Set `STATUS_ENDPOINT_API_KEY` from a secret store, because mock-jwks isn't available.
   - Limit the run to non-destructive tests such as ping, status and auth rejection.
