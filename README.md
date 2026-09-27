# Savings Account Opening Checklist Agent (`savings_account_agent`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.2.0-green.svg)](https://adk.dev)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

An enterprise-ready, read-only **Savings Account Opening Assistant** built with **Google Agent Development Kit (ADK)**, **Gemini**, **Agent Platform Sessions**, **Agent Platform Memory Bank**, and **Agent Runtime**.

---

## 1. Project Overview

The `savings_account_agent` provides interactive guidance to bank staff or customer service representatives as they complete the checklist required for opening a savings account.

> [!IMPORTANT]
> **Demo & Checklist Assistant Scope**:
> - This agent is strictly a **checklist assistant**.
> - It does **NOT** connect to a live banking core system.
> - It does **NOT** execute financial transactions or fund transfers.
> - It does **NOT** store real customer KYC documents or raw sensitive numbers.

---

## 2. Business Use Case

Opening a savings account requires gathering and verifying specific customer details. The agent systematically tracks progress across 9 required checklist items:

1. **Full Name**
2. **Date of Birth**
3. **Mobile Number**
4. **Address**
5. **PAN Availability**
6. **Identity Proof Availability**
7. **Address Proof Availability**
8. **Photograph Availability**
9. **Nominee Information**

Instead of storing raw sensitive documents, the agent tracks item statuses (`PROVIDED`, `PENDING`, `NOT_APPLICABLE`).

---

## 3. Architecture

```mermaid
graph TD
    User["User / Customer Rep"] --> SavingsAccountAgent["Savings Account Agent (savings_account_agent)"]
    
    subgraph Core Components
        SavingsAccountAgent --> Session["Agent Platform Sessions\n(Current Conversation State)"]
        SavingsAccountAgent --> Memory["Agent Platform Memory Bank\n(Long-Term Preferences)"]
        SavingsAccountAgent --> Tools["Checklist Tools\n(get, update, status, reset)"]
        SavingsAccountAgent --> Guardrails["Privacy Guardrails\n(Sensitive Data Detector)"]
    end
    
    Session --> AgentRuntime["Google Cloud Agent Runtime\n(Vertex AI Reasoning Engines)"]
    Memory --> AgentRuntime
    Tools --> AgentRuntime
```

---

## 4. Sessions (Agent Platform Sessions)

A **Session** maintains conversation history and current application progress (`session.state["checklist"]`).

- Preserves conversation context throughout account opening.
- Allows pausing and continuing applications seamlessly.
- State persists item statuses (`PROVIDED`, `PENDING`, `NOT_APPLICABLE`).

---

## 5. Memory Bank (Agent Platform Memory Bank)

**Memory Bank** retains long-term user preferences across multiple sessions (scoped by `user_id`).

### Allowed Memories
- User language preferences (e.g. "User prefers Telugu explanations").
- Interaction style (concise explanations, table formats).

### Prohibited Memories
- Raw PAN, Aadhaar, Credit/Debit card numbers, CVV, PIN, OTP, Passwords, or Account numbers.

---

## 6. Agent Runtime Deployment

The agent deploys natively to **Google Cloud Agent Runtime** (Vertex AI Reasoning Engines) via ADK (`agents-cli` / `google-cloud-aiplatform`).

- Containerized execution.
- Managed autoscaling and session persistence.
- Enterprise IAM and audit capability.

---

## 7. Checklist Workflow & Response Format

The agent renders progress using a clean, structured table format:

```text
Savings Account Checklist

✓ Full Name
✓ Date of Birth
✓ Mobile
○ Address
✓ PAN
○ Identity Proof
○ Address Proof
✓ Photograph
○ Nominee

Progress: 5/9

Next required item:
Address
```

---

## 8. Privacy Guardrails

Automatic regex patterns detect:
- **PAN** (`[A-Z]{5}[0-9]{4}[A-Z]{1}`)
- **Aadhaar** (12-digit number)
- **Credit/Debit Card** (13–19 digits)
- **CVV / PIN / OTP**
- **Bank Account Numbers**

### Privacy Actions
1. Replaces secret tokens with `[REDACTED_<TYPE>]`.
2. Emits privacy notice:
   > *"For privacy and security, sensitive information (PAN) has been marked as provided. The exact value will not be stored, logged, or repeated."*
3. Ensures raw values are purged before session data reaches Memory Bank or telemetry.

---

## 9. Tools

| Tool | Parameters | Description |
|------|------------|-------------|
| `get_account_checklist()` | None | Returns required checklist items array and `account_type="SAVINGS"`. |
| `update_checklist(item, status)` | `item: str`, `status: str` | Updates item status (`PROVIDED`, `PENDING`, `NOT_APPLICABLE`). |
| `get_checklist_status()` | None | Returns total count, completion percentage, next item, and formatted checklist table. |
| `reset_checklist()` | None | Resets current checklist to initial `PENDING` state for a new application. |

---

## 10. Local Development

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI API enabled

### Setup Environment
```bash
git clone https://github.com/vimalsagar007/savings-account-agent.git
cd savings-account-agent

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 11. Authentication & Environment

Set environment variables (no hardcoded keys):

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_ENTERPRISE="true"
export MODEL_NAME="gemini-2.5-flash"
export STAGING_BUCKET="gs://your-staging-bucket-name"
```

Authenticate with Google Application Default Credentials:
```bash
gcloud auth application-default login
```

---

## 12. Local FastAPI Server

Start the local test server:
```bash
uvicorn app:app --reload --port 8000
```

### Endpoints
- `GET /health`: Health check
- `POST /chat`: Send prompt to agent
- `GET /checklist`: Fetch checklist status
- `POST /checklist/reset`: Reset session checklist

---

## 13. Deployment to Agent Runtime

Deploy using `deploy.py`:
```bash
python3 deploy.py
```

Or via `agents-cli`:
```bash
agents-cli deploy --project $GOOGLE_CLOUD_PROJECT --region $GOOGLE_CLOUD_LOCATION --no-confirm-project
```

---

## 14. Testing

Run unit test suite:
```bash
pytest
```

Includes tests for:
- Checklist creation, updates, and resets
- Sensitive data detection & redaction
- Session context preservation
- Memory retrieval across sessions
- Verification that raw PAN values are excluded from Memory Bank

---

## 15. Demo Commands

### Session Continuation Demo
Demonstrates session creation, updating items, setting language preference, and continuing in a new session:
```bash
python3 scripts/session_demo.py
```

### Memory Bank & Privacy Demo
Demonstrates long-term memory retrieval ("Telugu explanations") and proves raw PAN values are never stored in Memory Bank:
```bash
python3 scripts/memory_demo.py
```

---

## 16. Example Conversation

**User**: *"I want to open a savings account."*  
**Agent**: *"Let's start the checklist! I will guide you through the process."*

**User**: *"My name is Rahul and my mobile number is 9876543210."*  
**Agent**: *"Marked Full Name and Mobile as provided!"*

**User**: *"My PAN is ABCDE1234F."*  
**Agent**:  
> *"PAN has been marked as provided. For privacy, I won't retain or repeat the PAN number."*

```text
Savings Account Checklist

✓ Full Name
○ Date of Birth
✓ Mobile
○ Address
✓ PAN
○ Identity Proof
○ Address Proof
○ Photograph
○ Nominee

Progress: 3/9

Next required item:
Date of Birth
```

---

## 17. Production Considerations

1. **Authentication & Authorization**: Integrate Identity-Aware Proxy (IAP) or OAuth 2.0 on the API endpoint.
2. **Audit Logging**: Enable Cloud Logging with sensitive payload filters.
3. **Database Sessions**: Replace `InMemorySessionService` with `VertexAiSessionService` or `DatabaseSessionService` for multi-instance horizontal scaling.
4. **Memory Bank Scoping**: Bind Memory Bank user IDs to verified enterprise IAM identities.
