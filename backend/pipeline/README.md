# Pipeline Service

Phase Two service that coordinates email forensic analysis, content/link analysis, attachment scoring, classification, correlation, evidence logging, and final score aggregation.

## Run

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100
```

The API is documented at `http://127.0.0.1:8100/docs`.

## Endpoints

- `POST /internal/analyze` — accepts the `EmailSubmission` contract and returns a completed `FraudAssessment` (`200`) or an async job (`202`) when a sandboxable attachment is present.
- `GET /internal/analysis/{submission_id}` — reads the current pipeline job and final assessment.
- `GET /internal/evidence/{submission_id}` — returns the append-only evidence events emitted by the pipeline.
- `GET /health` — reports service status and module versions.

The orchestrator calls the documented specialist APIs over HTTP. It loads `FORENSIC_API` and `ML_API` from the repository's `md/.env` file (or `PIPELINE_FORENSIC_API` / `PIPELINE_ML_API` environment variables). The Forensics and ML projects now expose the missing contract-compatible endpoints required by `docs/forensics-README.md` and `docs/aiml-README.md`.

For local development, run the three services with separate ports and point the two environment variables at the Forensics and ML base URLs. The pipeline test suite uses injected local adapters, so it never transmits test data to external URLs.
