# CVBoost

A complete FastAPI and Tailwind application for career self-assessment: PDF resume extraction, grounded skill-gap analysis, Sentence-BERT cosine similarity, and actionable Gemini recommendations. The original portfolio is a separate project and is not modified.

## Quick start (Python 3.12 recommended)

```powershell
cd cvboost
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install 'torch<3' 'torchvision<1' --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set GEMINI_API_KEY locally. Do not commit it.
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. Open **http://127.0.0.1:8000/docs** for interactive API documentation. `run.ps1` is an alternative launcher after setup. On macOS/Linux, use `.venv/bin/python` instead of `.venv\Scripts\python.exe`.

The compiled CSS is included, so Node is not required to run the app. For a lightweight UI/demo/test environment, install `requirements-dev.txt` instead of the full ML stack. Live analysis requires `requirements.txt` and a server-side API key. The clearly labelled sample analysis requires no key and makes no AI calls.

## Gemini model compatibility

Google shut down **Gemini 1.5 Flash on September 29, 2025**. The original research pipeline is retained, but `.env.example` defaults to **`GEMINI_MODEL=gemini-flash-latest`** through the official `google-genai` SDK. Configure another available model through `GEMINI_MODEL`; no model name is hardcoded in the analysis service. A retired or unavailable model returns an actionable service error, rather than fake results.

- Official retirement notice: https://ai.google.dev/gemini-api/docs/changelog#september-29-2025
- Current model lifecycle: https://ai.google.dev/gemini-api/docs/deprecations
- Structured output SDK: https://github.com/googleapis/python-genai

Create your key in Google AI Studio: https://aistudio.google.com/apikey. Put it in `.env` on the server; never in frontend JavaScript, a public repository, or a browser form.

## Project structure

```text
cvboost/
  main.py                    # Async API, multipart bounds, response/error handling
  config.py                  # Validated environment configuration
  schemas.py                 # Pydantic request/AI/response contracts
  services/
    parser.py                # PDF preflight + Unstructured fast extraction
    ai_engine.py             # Grounded extraction and coaching with Gemini
    embeddings.py            # Lazy MiniLM encoder and token-window pooling
    scoring.py               # Quote verification and deterministic coverage/total
    errors.py
  templates/index.html       # Responsive dashboard and accessible tabs
  static/
    src.css                  # Tailwind source and component styles
    css/app.css              # Compiled stylesheet, included for deployment
    js/app.js                # Uploads, dashboard rendering, tabs, evidence, export
    favicon.svg
  data/demo.json             # Fictional, precomputed example, clearly labelled
  scripts/build_demo.py       # Rebuild the sample fixture without external calls
  tests/test_app.py
  .env.example
  requirements*.txt
  package.json
  pnpm-lock.yaml
  Dockerfile
  run.ps1
```

## Processing pipeline

1. Validate consent, job description, PDF signature/type/size, encryption, page count, and selectable text.
2. Extract PDF elements locally with `unstructured.partition.pdf.partition_pdf(strategy="fast")`. Scanned/image-only PDFs are rejected with instructions to run OCR first; they are never silently treated as empty resumes.
3. Ask Gemini for a structured candidate profile and skill requirements with exact resume and job-description evidence quotes. Document contents are treated as untrusted data in the system instruction.
4. Reject requirements without a job-description quote. Mark a skill matched only when its resume quote exists in the extracted resume. Deduplicate skill names; required takes precedence over preferred.
5. Encode the **original** resume and **original** job description with `sentence-transformers/all-MiniLM-L6-v2`. Tokenize documents into overlapping model-length windows, encode all windows, pool their vectors, and calculate scikit-learn cosine similarity. Long resumes are not silently truncated to the model's first 256 tokens.
6. Compute deterministic skill coverage and the documented overall score. Ask Gemini for a narrative, concrete learning actions, and related role ideas using the checked results.
7. Render metrics, five section tabs, categorized skills, source evidence, and a growth roadmap. The JSON report can be downloaded locally.

The model and NLP resources are cached under `.cache/`, excluded from source packages. The first live request may need time and internet access for model/resource downloads. You can prewarm the encoder after installation:

```powershell
.\.venv\Scripts\python.exe -c "from config import Settings; from services.embeddings import SemanticEncoder; print(SemanticEncoder(Settings().embedding_model).score('Python and SQL data analysis', 'Data analyst using Python and SQL'))"
```

MiniLM's model card tags the requested checkpoint as **English**. Gemini can parse multilingual documents, but this checkpoint should not be represented as a validated multilingual encoder. For multilingual deployment, configure an appropriate Sentence-Transformers checkpoint and evaluate it on representative CV/JD pairs.

## Score definitions

All displayed scores are percentages from 0 to 100, not calibrated hiring probabilities.

- **Required skills:** matched required skills / total required skills × 100.
- **Preferred skills:** matched preferred skills / total preferred skills × 100.
- **Semantic embedding:** cosine similarity × 100, clipped to [0,100] for display.
- **Total match score:** 50% required coverage + 20% preferred coverage + 30% semantic score.

When a skill category has no explicit requirements, its coverage is **N/A**, not 0% or 100%; its component is excluded and remaining weights are normalized. The exact active weights are returned with each response and shown under “How your score is calculated.”

**The composite weights are an explicit implementation choice. The paper does not specify this formula.** Resume evidence verification reduces unsupported matches but does not prove proficiency. “Skills to improve” means not evidenced in the submitted text. Related roles are suggestions, not current job vacancies; no job-search API or vacancy database is configured.

## API

- `GET /`: rendered application.
- `GET /api/health`: configuration/dependency availability; no key values are returned. This does not perform a paid model probe.
- `GET /api/demo`: fictional example; set `ENABLE_DEMO=false` to disable it.
- `POST /api/analyze`: multipart fields `resume` (PDF), `job_description` (80–12,000 characters by default), `consent=true`.

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -F "resume=@my-resume.pdf;type=application/pdf" \
  -F "job_description=Paste a complete job description with at least eighty characters here, including required and preferred skills." \
  -F "consent=true"
```

Responses use `AnalysisResponse` in `schemas.py`. Errors have the shape `{"error":{"code":"...","message":"..."}}`: 413 for upload size, 415 for file type, 422 for invalid input/PDF, 429 for busy/quota, 502 for invalid/upstream AI responses, 503 for missing configuration/dependencies/model, and 504 for timeouts. Raw prompts, resumes, API keys, and upstream response bodies are not written to application logs or echoed in error responses.

Gemini receives a compact JSON schema with field types, enums, required fields, and object structure. Nested string-length and array-size constraints are enforced by the original Pydantic models after generation, rather than sent to Gemini's decoder: combining those constraints caused HTTP 400 responses with the current Flash model. Invalid or oversized generated data still fails validation. Provider HTTP 400 and 504 responses now produce specific analysis-format and timeout errors.

## UI and CSS development

```bash
npm install
npm run build:css
# Or: npm run watch:css
```

Tailwind 3.4.17 is pinned; the output CSS is committed/included. All model text is inserted into the DOM with `textContent`, not HTML. The UI supports PDF drag/drop, file removal, loading/error/empty/sample states, keyboard-operated tabs, resume evidence, JSON export, a help dialog, and reduced-motion preferences. Changing inputs marks an earlier analysis as out of date.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Tests cover upload boundaries, missing consent/configuration, malformed and encrypted/scanned PDFs, chunked request size limits, privacy of validation errors, quote grounding/deduplication, missing-category score normalization, API orchestration, invalid AI JSON, and disabled demo mode. External Gemini calls are isolated in tests; these do not substitute for a live API acceptance test using your own key.

## Deployment and data handling

This application needs a **Python server**. GitHub can store the source, but GitHub Pages cannot execute FastAPI. Deploy the Docker image or a Python service to a host supporting long-running Python workloads and sufficient memory for the local models.

```bash
docker build -t cvboost .
docker run --rm -p 8000:8000 --env-file .env cvboost
```

Use a single worker initially; each worker otherwise loads its own model. Add HTTPS and deployment-level authentication/rate limits before accepting public uploads. Request size and concurrency are bounded in this application; they are not a substitute for a hardened multi-user upload gateway.

Uploaded files are closed/deleted after requests; CVBoost keeps no resume history or analysis database. Extracted text and the target job description are sent to Google Gemini only after the user checks consent and clicks Process. Google's service terms and retention policies also apply. The demo uses fictional information and never sends your selected resume anywhere. No PDF from the author’s Downloads folder is bundled or uploaded.

## Research basis and references

Based on the CVBoost essay by **Satya Bintang Esa Resiadi and Mutia Septianingsih**, Statistics, Universitas Sebelas Maret. Its PDF appendix provides the original dark input/results layout and the five tabs. This implementation preserves the requested architecture and makes the scoring, grounding checks, model migration, and demo behavior explicit. It does not claim to reproduce the paper's experimental results or a validated employment outcome.

- Sentence-Transformers model card: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Unstructured PDF strategies: https://docs.unstructured.io/open-source/core-functionality/partitioning
- FastAPI documentation: https://fastapi.tiangolo.com/
- Gemini structured-output schema limitations: https://ai.google.dev/gemini-api/docs/generate-content/structured-output#limitations
