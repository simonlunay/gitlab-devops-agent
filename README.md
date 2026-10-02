# GitLab DevOps Agent

**An autonomous DevOps agent that diagnoses CI/CD failures, triages issues, reviews merge requests, and writes release notes from plain-English commands.**

Built with Google ADK and Gemini 2.5 Flash on Vertex AI, integrated with GitLab's official MCP server, and containerized for Google Cloud Run. Built for the Google Cloud Rapid Agent Hackathon.

![Demo](./assets/demo.gif)
<!-- Replace with a 10 to 15 second GIF: ask it to diagnose a failed pipeline, show the root cause it finds -->

> **No hosted demo.** The agent runs on my own API credentials, so there's no public instance. You can run it locally with your own keys in a few minutes (see [Run it yourself](#run-it-yourself)).

---

## What it does

| Capability | Description |
|---|---|
| **Diagnose Pipeline** | Pulls failed job logs from a CI/CD pipeline and surfaces the root cause |
| **Auto-Triage Issues** | Scans every open issue, infers labels and priority, and posts a triage comment |
| **Triage Issue** | Analyzes a single issue and suggests labels and priority |
| **Review Merge Request** | Summarizes changed files, reviewers, approvals, and description |
| **Merge Merge Request** | Merges an MR after verifying it's in a mergeable state |
| **Generate Release Notes** | Produces categorized markdown release notes from merged MRs over a date range |
| **Issue Management** | Lists issues with age, priority, and stale flags; comments on and closes issues |

On top of these custom tools, the agent connects to **GitLab's official MCP server**, giving it GitLab's full native tool surface alongside its own.

## Architecture

```
            ┌────────────────────────┐
            │   ADK Web UI / Chat    │
            └───────────┬────────────┘
                        │
            ┌───────────▼────────────┐
            │   Gemini 2.5 Flash     │  (Vertex AI)
            │   agentic tool loop    │
            └─────┬────────────┬─────┘
                  │            │
      ┌───────────▼───┐   ┌────▼──────────────┐
      │ Custom tools  │   │ GitLab MCP server │
      │ (python-gitlab)│  │ (official)        │
      └───────┬───────┘   └────┬──────────────┘
              │                │
         ┌────▼────────────────▼────┐
         │       GitLab REST API     │
         │ issues · MRs · pipelines  │
         └───────────────────────────┘
```

## Tech stack

| Component | Technology |
|---|---|
| Agent framework | Google Agent Development Kit (ADK) 2.0 |
| LLM | Gemini 2.5 Flash via Vertex AI |
| Tool protocol | GitLab's official Model Context Protocol (MCP) server |
| GitLab client | python-gitlab |
| Runtime | Python 3.11+ |
| Deployment | Docker, Google Cloud Run (secrets via Secret Manager) |

## Example prompts

```
Diagnose pipeline 998 in project my-org/my-repo
Auto-triage all open issues in project my-org/my-repo
Review merge request !17 in project my-org/my-repo
Generate release notes for my-org/my-repo since 2025-01-01
```

---

## Run it yourself

**Requirements:** Python 3.11+, a GitLab personal access token (`api` scope, or `read_api` for read-only), and a Google Cloud project with Vertex AI enabled.

```bash
git clone https://github.com/simonlunay/gitlab-devops-agent.git
cd gitlab-devops-agent
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `gitlab_agent/.env`:

```env
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_URL=https://gitlab.com
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_GENAI_USE_VERTEXAI=1
```

Then run:

```bash
adk web
```

Open http://localhost:8000 and select **gitlab_devops_agent**.

<details>
<summary><b>Docker and Cloud Run</b></summary>

```bash
docker build -t gitlab-devops-agent .
docker run -p 8080:8080 \
  -e GITLAB_TOKEN=your_token \
  -e GITLAB_URL=https://gitlab.com \
  -e GOOGLE_CLOUD_PROJECT=your_project_id \
  -e GOOGLE_GENAI_USE_VERTEXAI=1 \
  gitlab-devops-agent
```

```bash
gcloud run deploy gitlab-devops-agent \
  --source . --region us-central1 --port 8080 \
  --set-env-vars GITLAB_URL=https://gitlab.com,GOOGLE_GENAI_USE_VERTEXAI=1 \
  --set-secrets GITLAB_TOKEN=gitlab-token:latest,GOOGLE_CLOUD_PROJECT=gcp-project:latest
```

Cloud Run environment variables take precedence over a local `.env`.
</details>

## Project structure

```
gitlab-devops-agent/
├── gitlab_agent/
│   ├── agent.py    # Agent definition, tool registration, MCP server config
│   └── tools.py    # GitLab API tool implementations
├── Dockerfile
└── requirements.txt
```

## Security notes

- Credentials live only in `.env` locally or in Secret Manager on Cloud Run, never in code
- The same scoped token authenticates both the custom tools and the MCP server
- `auto_triage_all_issues` is a write operation: it modifies labels and comments on every open issue in the target project

---

Built by [Simon Lunay](https://www.simonlunay.com) · [LinkedIn](https://www.linkedin.com/in/simonlunay) · MIT License
