# Verification

Verified locally on Windows with Python 3.12.

- FastAPI home, health, sample analysis, compiled CSS, and API documentation serve successfully.
- **23 automated tests passed.** They cover API/file boundaries, consent/configuration errors, request body size bounds, source quote checks, skill deduplication, score normalization, service orchestration, invalid AI JSON, compact Gemini schemas with strict local length validation, private/actionable HTTP 400 and 504 errors, disabled demo mode, and long-document token-window pooling.
- The installed environment passed `pip check` with no broken requirements.
- The JavaScript passes the Node syntax check. The Tailwind production stylesheet was compiled successfully and is included.
- Real Unstructured extraction processed an in-memory, fictional one-page PDF: 322 text characters were extracted with the expected skill text. No personal document was sent to an external API.
- The real `sentence-transformers/all-MiniLM-L6-v2` CPU model loaded successfully. Identical sentence pairs scored **100.00%**; an unrelated marine-biology sentence against a Python/SQL analytics sentence scored **12.83%**. This is a smoke test, not a scientific evaluation or reproduction of the paper's experiments.
- The browser sample returned 72.8% total, 83.3% required coverage, 33.3% preferred coverage, and 81.6% illustrative semantic similarity. It is explicitly labelled fictional and precomputed.
- Tested all five tabs, keyboard arrow navigation, evidence display, missing-upload feedback, the help dialog, and invalidation of results after changing the input.
- Checked the 1280 px desktop dashboard and 375 px phone layout: no horizontal page overflow. The phone tab strip scrolls within its own container.
- On 2026-10-21, a real structured-extraction request using fictional CV/job text succeeded with `gemini-flash-latest` (reported model version `gemini-3.8-flash`). The original bounded decoder schema returned HTTP 400; removing decoder string/list bounds while retaining Pydantic validation resolved that request. No credentials are included in this report or the source ZIP.
- A full live `POST /api/analyze` with an in-memory fictional one-page PDF returned HTTP 200: live mode, five assessed skills, a 71.24% total score, 70.8% semantic similarity, and two action steps. The first complete request after restarting the server took 166.3 seconds, including PDF extraction, semantic-model initialization, and both Gemini calls. These example scores are smoke-test observations, not expected scores for a real candidate.

## Limit of verification

Automated tests isolate Gemini with explicit fakes; the live smoke test above used a server-side key and fictional data. Account quota/billing and the quality of generated career guidance still need evaluation for the intended deployment. A successful request does not guarantee future model availability or hiring outcomes. Without a configured key, the app returns a clear configuration error instead of producing pretend live results.

The Dockerfile is provided but the image was not built in this environment. Deployment and TLS/authentication configuration depend on the target host. Temporary browser-test fixtures, Python environments, model caches, and node_modules are excluded from the deliverable ZIP.
