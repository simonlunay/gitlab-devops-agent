import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams
from google.genai import types
from gitlab_agent.tools import (
    list_issues,
    review_merge_request,
    triage_issue,
    diagnose_pipeline,
    generate_release_notes,
    close_issue,
    add_issue_comment,
    merge_merge_request,
    auto_triage_all_issues,
)

load_dotenv()

root_agent = Agent(
    name="gitlab_devops_agent",
    model="gemini-2.5-flash",
    description="An autonomous GitLab DevOps assistant that reviews PRs, triages issues, diagnoses CI/CD failures, and generates release notes.",
    instruction="""
    You are an autonomous GitLab DevOps assistant. You help software teams by:
    1. Reviewing merge requests and flagging code issues
    2. Triaging new issues by labeling and prioritizing them
    3. Diagnosing CI/CD pipeline failures and suggesting fixes
    4. Generating release notes from merged merge requests

    Always be concise and actionable. When given a GitLab project ID, use your tools to fetch real data before responding.
    """,
    tools=[
        list_issues,
        review_merge_request,
        triage_issue,
        diagnose_pipeline,
        generate_release_notes,
        close_issue,
        add_issue_comment,
        merge_merge_request,
        auto_triage_all_issues,
        McpToolset(
            connection_params=SseConnectionParams(
                url="https://gitlab.com/-/llm/mcp",
                headers={"Authorization": f"Bearer {os.getenv('GITLAB_TOKEN')}"},
            )
        ),
    ]
)