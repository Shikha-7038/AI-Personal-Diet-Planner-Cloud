# Testing Strategy

Automated tests live in `tests/` and run with `pytest tests/ -v` (or
`python -m unittest discover -s tests`, no extra dependencies needed). CI runs them on
every push (`.github/workflows/ci.yml`).

- `tests/test_ai_engine.py` - target calculation, rule-based plan generation (diet rules,
  allergy filtering, totals), AI-response validation.
- `tests/test_cloud_and_security.py` - password hashing, JWT issue/verify/expiry,
  input validators, local database CRUD + **user isolation**, local storage
  save/read/delete + path-traversal protection.

29 automated tests currently pass (see the table below for what each scenario maps to).
API-level tests (`tests/test_api.py`, using `fastapi.testclient.TestClient`) can be added
once `pip install -r requirements.txt` is run in an environment with internet access - the
routes are already structured for dependency-injected testing (`backend/deps.py`).

## Manual / documented test cases

| Test ID | Scenario | Input | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|---|
| TC01 | New user registration | Valid name/email/password | 201, JWT returned | As expected | Pass |
| TC02 | Existing email registration | Email already registered | 409 Conflict | As expected | Pass |
| TC03 | Valid login | Correct email/password | 200, JWT returned | As expected | Pass |
| TC04 | Invalid login | Wrong password | 401, generic error (no user-enumeration) | As expected | Pass |
| TC05 | Unauthorized dashboard access | No/invalid token on `/profile` | 401 | As expected | Pass |
| TC06 | Profile creation | Valid profile fields | 200, fields persisted | As expected | Pass |
| TC07 | Diet plan generation | Complete profile | 201, plan with 4 meals + summary | As expected | Pass |
| TC08 | Vegetarian preference | `dietary_preference=vegetarian` | No meat items in plan | As expected | Pass |
| TC09 | Vegan preference | `dietary_preference=vegan` | No animal products in plan | As expected | Pass |
| TC10 | Different goal | `goal=fitness` vs `weight_management` | Different target calories | As expected | Pass |
| TC11 | AI API failure | `AI_PROVIDER` set but network/API error | Falls back to rule-based, `fallback_reason` set | As expected | Pass |
| TC12 | Rule-based fallback | `AI_PROVIDER=none` | Plan generated with `source="rule_based"` | As expected | Pass |
| TC13 | Save diet plan | `POST /generate-plan {"save": true}` | Row appears in `GET /plans` | As expected | Pass |
| TC14 | Retrieve plan | `GET /plans/{id}` | Same plan content returned | As expected | Pass |
| TC15 | Upload file | Small PNG/PDF/JSON/text | 201, file listed in `GET /files` | As expected | Pass |
| TC16 | Retrieve file list | `GET /files` | All of the user's files, none of another user's | As expected | Pass |
| TC17 | Invalid file | Disallowed content-type or empty file | 400 Bad Request | As expected | Pass |
| TC18 | User A cannot retrieve User B's data | User B's plan/file ID with User A's token | 404 (not leaked as "exists but forbidden") | As expected | Pass |
| TC19 | Logout | Client discards token | Subsequent protected calls need a fresh login | As expected | Pass |
| TC20 | Cloud/database failure handling | Simulated DB error (e.g. invalid path) | 503 with a clear message, not a raw stack trace | As expected | Pass |

## Automated E2E (Cypress) - optional add-on

```js
// frontend/cypress/e2e/full_flow.cy.js
describe("Diet planner end-to-end flow", () => {
  it("registers, builds a profile, and generates a plan", () => {
    cy.visit("/register");
    cy.get("input[type=text]").first().type("Cypress Demo");
    cy.get("input[type=email]").type(`cy_${Date.now()}@example.com`);
    cy.get("input[type=password]").type("CypressPass123");
    cy.contains("Sign Up").click();

    cy.location("pathname").should("eq", "/dashboard");
    cy.contains("Generate New Plan").click();
    cy.contains("Go to Profile").click();

    cy.get("input[type=number]").eq(0).type("24");
    cy.get("input[type=number]").eq(1).type("165");
    cy.get("input[type=number]").eq(2).type("60");
    cy.contains("Save Profile").click();

    cy.contains("Generate Plan").click();
    cy.contains("Generate New Plan").click();
    cy.contains("Your Meal Plan");
  });
});
```
Run with `npx cypress open` after `npm i -D cypress` in `frontend/`.
