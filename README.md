# GitLab DevOps Agent

An autonomous AI-powered DevOps assistant built with **Google ADK 2.0** and **Gemini 2.5 Flash**. It connects directly to your GitLab instance and performs real engineering tasks: reviewing code, triaging issues, diagnosing pipeline failures, and more. All through natural language.

---

## Live Demo

Try the agent live — no setup required:

**[gitlab-devops-agent-792314829007.us-central1.run.app](https://gitlab-devops-agent-792314829007.us-central1.run.app)**

> Deployed on Google Cloud Run. Point it at any public GitLab project and start asking questions.

---

## Features

| Capability | Description |
|---|---|
| **List Issues** | Fetch all open issues with age, inferred priority, and stale flags |
| **Triage Issue** | Analyze a single issue and suggest labels and priority based on content |
| **Auto-Triage All Issues** | Bulk-scan every open issue, apply inferred labels, and post a triage comment |
| **Add Issue Comment** | Post a comment on any issue programmatically |
| **Close Issue** | Close an open issue by state transition |
| **Review Merge Request** | Summarize an MR's changed files, reviewers, approvals, and description |
| **Merge Merge Request** | Merge an open MR after verifying it is in a mergeable state |
| **Diagnose Pipeline** | Fetch failed job logs from a CI/CD pipeline and surface the root cause |
| **Generate Release Notes** | Produce categorized markdown release notes from merged MRs over a date range |

The agent also connects to **GitLab's official MCP server** (`https://gitlab.com/-/llm/mcp`), giving it access to GitLab's full native tool surface alongside the custom tools above.

---

## Tech Stack

- [Google Agent Development Kit (ADK) 2.0](https://google.github.io/adk-docs/)
- [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) via Vertex AI
- [GitLab MCP Server](https://docs.gitlab.com/ee/user/gitlab_duo/mcp/) — GitLab's official Model Context Protocol server
- [Python 3.11+](https://www.python.org/)
- [python-gitlab](https://python-gitlab.readthedocs.io/) — GitLab REST API client
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management
- [Docker](https://www.docker.com/) + [Google Cloud Run](https://cloud.google.com/run) — containerised deployment

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/gitlab-devops-agent.git
cd gitlab-devops-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file inside the `gitlab_agent/` directory:

```env
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_URL=https://gitlab.com
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_GENAI_USE_VERTEXAI=1
```

| Variable | Description |
|---|---|
| `GITLAB_TOKEN` | GitLab Personal Access Token with `api` scope — also used to authenticate the MCP server |
| `GITLAB_URL` | Your GitLab instance URL (use `https://gitlab.com` for GitLab.com) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for Vertex AI access |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `1` for Vertex AI, `0` for Gemini API (AI Studio) |

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

To create a GitLab Personal Access Token: **GitLab → User Settings → Access Tokens → Add new token** with the `api` scope.

---

## Running the Agent

### Locally

```bash
adk web
```

Open [http://localhost:8000](http://localhost:8000) and select **gitlab_devops_agent**.

### Docker

```bash
docker build -t gitlab-devops-agent .
docker run -p 8080:8080 \
  -e GITLAB_TOKEN=your_token \
  -e GITLAB_URL=https://gitlab.com \
  -e GOOGLE_CLOUD_PROJECT=your_project_id \
  -e GOOGLE_GENAI_USE_VERTEXAI=1 \
  gitlab-devops-agent
```

Open [http://localhost:8080](http://localhost:8080).

### Google Cloud Run

```bash
gcloud run deploy gitlab-devops-agent \
  --source . \
  --region us-central1 \
  --port 8080 \
  --set-env-vars GITLAB_URL=https://gitlab.com,GOOGLE_GENAI_USE_VERTEXAI=1 \
  --set-secrets GITLAB_TOKEN=gitlab-token:latest,GOOGLE_CLOUD_PROJECT=gcp-project:latest
```

Environment variables set by Cloud Run take precedence over any local `.env` file.

---

## Example Prompts

```
List all open issues in project my-org/my-repo
```
```
Triage issue #42 in project my-org/my-repo
```
```
Auto-triage all open issues in project my-org/my-repo
```
```
Review merge request !17 in project my-org/my-repo
```
```
Diagnose pipeline 998 in project my-org/my-repo
```
```
Generate release notes for my-org/my-repo since 2025-01-01
```

---

## Project Structure

```
gitlab-devops-agent/
├── gitlab_agent/
│   ├── agent.py       # ADK agent definition, tool registration, and MCP server config
│   ├── tools.py       # GitLab API tool implementations
│   └── .env           # Local environment variables (not committed)
├── Dockerfile
├── .dockerignore
└── README.md
```

---

## Security

- Store credentials exclusively in `.env` locally, or as Cloud Run secrets in production — never hard-code tokens.
- Grant the GitLab token the minimum required scope (`api` for full access, or `read_api` for read-only use cases). The same token authenticates both the python-gitlab tools and the GitLab MCP server.
- Treat `auto_triage_all_issues` as a write operation — it modifies labels and posts a comment on every open issue in the target project.
