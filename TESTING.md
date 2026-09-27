# Testing & Verification Guide for `savings_account_agent`

This document provides a comprehensive step-by-step guide to test and verify all features of the **Savings Account Opening Checklist Agent**.

---

## Quick Reference Commands

| Test Type | Command | Description |
| --- | --- | --- |
| **Unit Tests** | `pytest -v` | Runs all 16 automated unit tests |
| **Session Demo** | `PYTHONPATH=. python3 scripts/session_demo.py` | Tests session continuation & language preferences |
| **Memory & Privacy Demo** | `PYTHONPATH=. python3 scripts/memory_demo.py` | Tests Memory Bank & verifies zero PAN leakage |
| **FastAPI Server** | `uvicorn app:app --reload --port 8000` | Launches local REST API server |
| **Deployed Cloud Test** | `agents-cli run --deployment-target agent_runtime` | Queries live Google Cloud deployment |

---

## 1. Automated Unit Tests (`pytest`)

Run the complete unit test suite:

```bash
pytest -v
```

### Expected Output
```text
======================== 16 passed in 0.94s =========================
```

### Coverage Breakdown
1. `tests/test_checklist.py`:
   - `test_get_account_checklist`: Verifies required 9 checklist items.
   - `test_update_checklist`: Verifies updating item statuses (`PROVIDED`, `PENDING`).
   - `test_update_checklist_invalid_item`: Verifies error handling on unknown items.
   - `test_update_checklist_invalid_status`: Verifies error handling on invalid status values.
   - `test_get_checklist_status`: Verifies table generation format and percentage completion.
   - `test_reset_checklist`: Verifies resetting checklist to initial state.

2. `tests/test_privacy.py`:
   - `test_detect_pan`: Detects standard Indian PAN pattern (`[A-Z]{5}[0-9]{4}[A-Z]{1}`).
   - `test_detect_aadhaar`: Detects 12-digit Aadhaar pattern.
   - `test_detect_card_number`: Detects credit/debit card numbers.
   - `test_detect_cvv_and_otp`: Detects CVV/PIN/OTP patterns.
   - `test_sanitize_pan_text`: Verifies raw token replacement with `[REDACTED_PAN]`.
   - `test_process_sensitive_input`: Verifies privacy notice generation.

3. `tests/test_session.py`:
   - `test_session_context_and_state`: Verifies state initialization in ADK `Session`.
   - `test_session_continuation`: Verifies resuming state across multiple conversation turns.

4. `tests/test_memory.py`:
   - `test_memory_retrieval_and_preference`: Verifies long-term preference storage across sessions.
   - `test_pan_value_not_stored_in_memory`: Performs privacy audit confirming raw PAN values are excluded from Memory Bank.

---

## 2. Interactive Demonstration Scripts

### A. Session Continuation & Preference Tracking (`scripts/session_demo.py`)
Run the script:

```bash
PYTHONPATH=. python3 scripts/session_demo.py
```

**Verifies:**
- **Turn 1**: User provides name and mobile number.
- **Turn 2**: User requests explanations in **Telugu** ("I want explanations in Telugu").
- **Turn 3**: User resumes in a new session (`session_2`), and the agent remembers previous checklist items and responds in Telugu.

### B. Memory Bank Privacy Audit (`scripts/memory_demo.py`)
Run the script:

```bash
PYTHONPATH=. python3 scripts/memory_demo.py
```

**Verifies:**
- Queries Memory Bank for user language preferences across sessions.
- Audits Memory Bank search results to ensure raw sensitive data (`ABCDE1234F`) was **never** indexed or stored.

---

## 3. Local FastAPI Service Testing (`curl`)

Start the local server in terminal 1:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

In terminal 2, execute the following commands:

### A. Health Check
```bash
curl -s http://localhost:8000/health | jq
```
*Response:*
```json
{
  "status": "healthy",
  "agent": "savings_account_agent"
}
```

### B. Interactive Chat (`POST /chat`)
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hi, my name is Rahul and my mobile number is 9876543210.",
    "user_id": "user_demo",
    "session_id": "sess_001"
  }' | jq
```

### C. Check Checklist Status (`GET /checklist`)
```bash
curl -s "http://localhost:8000/checklist?user_id=user_demo&session_id=sess_001" | jq
```

### D. Reset Checklist (`POST /checklist/reset`)
```bash
curl -s -X POST "http://localhost:8000/checklist/reset?user_id=user_demo&session_id=sess_001" | jq
```

---

## 4. Deployed Google Cloud Agent Runtime Testing

Test the live deployment on Vertex AI Reasoning Engines:

```bash
agents-cli run \
  --deployment-target agent_runtime \
  --project qwiklabs-gcp-02-63b2f55175ee \
  --region us-central1 \
  "I want to open a savings account"
```

Or view and test via Google Cloud Console:
👉 **[Google Cloud Console - Vertex AI Agent Engines](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/5716962935423631360?project=qwiklabs-gcp-02-63b2f55175ee)**
