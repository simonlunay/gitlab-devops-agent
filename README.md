# GitLab DevOps Agent

An autonomous AI-powered DevOps assistant built with **Google ADK 2.0** and **Gemini 2.5 Flash**. It connects directly to your GitLab instance and performs real engineering tasks: reviewing code, triaging issues, diagnosing pipeline failures, and more. All through natural language.

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

---

## Tech Stack

- [Google Agent Development Kit (ADK) 2.0](https://google.github.io/adk-docs/)
- [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) via Google AI / Vertex AI
- [Python 3.11+](https://www.python.org/)
- [python-gitlab](https://python-gitlab.readthedocs.io/) — GitLab REST API client
- [python-dotenv](https://pypi.org/project/python-dotenv/) — environment variable management

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
pip install google-adk python-gitlab python-dotenv
```

### 4. Configure environment variables

Create a `.env` file inside the `gitlab_agent/` directory:

```bash
cp gitlab_agent/.env.example gitlab_agent/.env
```

Then fill in your credentials:

```env
GITLAB_TOKEN=your_gitlab_personal_access_token
GITLAB_URL=https://gitlab.com
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_GENAI_USE_VERTEXAI=1
```

| Variable | Description |
|---|---|
| `GITLAB_TOKEN` | GitLab Personal Access Token with `api` scope |
| `GITLAB_URL` | Your GitLab instance URL (use `https://gitlab.com` for GitLab.com) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for Vertex AI access |
| `GOOGLE_GENAI_USE_VERTEXAI` | Set to `1` to use Vertex AI, `0` for Gemini API (AI Studio) |

> **Never commit your `.env` file.** It is already listed in `.gitignore`.

To create a GitLab Personal Access Token: **GitLab → User Settings → Access Tokens → Add new token** with the `api` scope.

---

## Running the Agent

Start the ADK web interface from the project root:

```bash
adk web
```

Then open [http://localhost:8000](http://localhost:8000) in your browser and select **gitlab_devops_agent** from the agent list.

### Example prompts

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
│   ├── agent.py       # ADK agent definition and tool registration
│   ├── tools.py       # GitLab API tool implementations
│   └── .env           # Local environment variables (not committed)
└── README.md
```

---

## Security

- Store credentials exclusively in `.env` — never hard-code tokens in source files.
- Grant the GitLab token the minimum required scope (`api` for full access, or narrow to `read_api` for read-only use cases).
- Treat `auto_triage_all_issues` as a write operation — it modifies labels and posts comments on every open issue in the target project.
