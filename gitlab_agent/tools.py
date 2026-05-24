import gitlab
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

gl = gitlab.Gitlab(
    os.getenv("GITLAB_URL"),
    private_token=os.getenv("GITLAB_TOKEN")
)

_PRIORITY_KEYWORDS = {
    "critical": ["critical", "crash", "data loss", "security", "outage", "breach", "vulnerability"],
    "high":     ["regression", "broken", "urgent", "blocker", "production", "p1", "hotfix"],
    "medium":   ["performance", "slow", "error", "failure", "bug", "incorrect", "wrong"],
    "low":      ["typo", "cosmetic", "minor", "enhancement", "improvement", "refactor"],
}

_LABEL_KEYWORDS = {
    "bug":         ["bug", "broken", "crash", "error", "failure", "regression", "not working"],
    "security":    ["security", "vulnerability", "cve", "exploit", "injection", "auth"],
    "performance": ["slow", "performance", "latency", "timeout", "memory", "cpu"],
    "documentation": ["docs", "documentation", "readme", "typo", "spelling"],
    "feature":     ["feature", "enhancement", "add", "new", "implement", "support"],
    "ci/cd":       ["pipeline", "ci", "cd", "deploy", "build", "test failure"],
}

def _days_ago(iso_timestamp: str) -> int:
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days

def _infer_priority(text: str) -> str:
    lower = text.lower()
    for priority, keywords in _PRIORITY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return priority
    return "medium"

def _infer_labels(text: str) -> list[str]:
    lower = text.lower()
    return [label for label, keywords in _LABEL_KEYWORDS.items() if any(kw in lower for kw in keywords)]


def list_issues(project_id: str) -> str:
    """Lists all open issues in a GitLab project with age and priority hints."""
    project = gl.projects.get(project_id)
    issues = project.issues.list(state="opened", all=True, order_by="created_at", sort="asc")

    if not issues:
        return f"No open issues found in project {project_id}."

    lines = [f"## Open Issues — {project.name_with_namespace}\n"]
    for issue in issues:
        labels = ", ".join(issue.labels) if issue.labels else "none"
        age = _days_ago(issue.created_at)
        text = f"{issue.title} {issue.description or ''}"
        priority = _infer_priority(text)
        age_flag = " ⚠ STALE" if age > 30 else ""
        lines.append(
            f"#{issue.iid} [{priority.upper()}] {issue.title}{age_flag}\n"
            f"  Age: {age}d | Author: {issue.author['name']} | Labels: {labels}\n"
            f"  URL: {issue.web_url}"
        )

    lines.append(f"\nTotal: {len(issues)} open issue(s)")
    return "\n".join(lines)


def review_merge_request(project_id: str, mr_iid: int) -> str:
    """Reviews a merge request and flags potential issues."""
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)
    changes = mr.changes()

    file_list = "\n".join(
        f"  - {c['new_path']} (+{c['diff'].count(chr(10) + '+')} / -{c['diff'].count(chr(10) + '-')})"
        for c in changes["changes"]
    )
    age = _days_ago(mr.created_at)
    reviewers = ", ".join(r["name"] for r in mr.reviewers) if mr.reviewers else "none assigned"
    approvals = mr.approvals_before_merge or 0

    return (
        f"## MR Review: {mr.title} (!{mr_iid})\n\n"
        f"**Author:** {mr.author['name']} | **Branch:** `{mr.source_branch}` → `{mr.target_branch}`\n"
        f"**State:** {mr.state} | **Age:** {age} day(s) | **URL:** {mr.web_url}\n"
        f"**Reviewers:** {reviewers} | **Approvals required:** {approvals}\n\n"
        f"### Changed Files ({len(changes['changes'])})\n{file_list}\n\n"
        f"### Description\n{mr.description or '(no description)'}\n\n"
        f"### Labels\n{', '.join(mr.labels) if mr.labels else 'none'}"
    )


def triage_issue(project_id: str, issue_iid: int) -> str:
    """Triages an issue by suggesting labels and priority based on content keywords."""
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_iid)

    text = f"{issue.title} {issue.description or ''}"
    suggested_priority = _infer_priority(text)
    suggested_labels = _infer_labels(text)
    age = _days_ago(issue.created_at)
    existing_labels = ", ".join(issue.labels) if issue.labels else "none"
    new_labels = [l for l in suggested_labels if l not in issue.labels]

    return (
        f"## Triage: {issue.title} (#{issue.iid})\n\n"
        f"**Author:** {issue.author['name']}\n"
        f"**State:** {issue.state} | **Age:** {age} day(s)\n"
        f"**URL:** {issue.web_url}\n\n"
        f"### Description\n{issue.description or '(no description)'}\n\n"
        f"### Current Labels\n{existing_labels}\n\n"
        f"### Suggested Priority\n{suggested_priority.upper()}\n\n"
        f"### Suggested Labels to Add\n"
        + (", ".join(new_labels) if new_labels else "none — existing labels look sufficient") +
        f"\n\n### Triage Notes\n"
        f"Priority inferred from title/description keywords. Review description above and assign "
        f"milestone or assignee if priority is HIGH or CRITICAL."
    )


def diagnose_pipeline(project_id: str, pipeline_id: int) -> str:
    """Diagnoses a failed CI/CD pipeline, including failed job logs."""
    project = gl.projects.get(project_id)
    pipeline = project.pipelines.get(pipeline_id)
    jobs = pipeline.jobs.list(all=True)

    failed_jobs = [j for j in jobs if j.status == "failed"]
    passed_jobs  = [j for j in jobs if j.status == "success"]
    skipped_jobs = [j for j in jobs if j.status == "skipped"]

    lines = [
        f"## Pipeline #{pipeline_id} Diagnosis\n",
        f"**Status:** {pipeline.status} | **Ref:** {pipeline.ref}",
        f"**Created:** {pipeline.created_at}",
        f"**Passed:** {len(passed_jobs)} | **Failed:** {len(failed_jobs)} | **Skipped:** {len(skipped_jobs)}\n",
    ]

    if not failed_jobs:
        lines.append("No failed jobs found.")
        return "\n".join(lines)

    for job in failed_jobs:
        lines.append(f"---\n### Failed Job: `{job.name}` (stage: {job.stage})")
        lines.append(f"**Duration:** {job.duration}s | **Runner:** {job.runner['description'] if job.runner else 'unknown'}")
        try:
            full_job = project.jobs.get(job.id)
            log = full_job.trace().decode("utf-8", errors="replace")
            # Keep the last 100 lines — most failures surface at the end
            tail = "\n".join(log.splitlines()[-100:])
            lines.append(f"\n**Log (last 100 lines):**\n```\n{tail}\n```")
        except Exception as e:
            lines.append(f"_(Could not fetch log: {e})_")

    return "\n".join(lines)


def generate_release_notes(project_id: str, from_date: str) -> str:
    """Generates formatted markdown release notes from merged MRs since from_date (ISO 8601)."""
    project = gl.projects.get(project_id)
    mrs = project.mergerequests.list(state="merged", updated_after=from_date, all=True, order_by="merged_at", sort="asc")

    if not mrs:
        return f"No merged MRs found in project {project_id} since {from_date}."

    buckets: dict[str, list] = {
        "Features": [],
        "Bug Fixes": [],
        "Security": [],
        "Performance": [],
        "CI/CD": [],
        "Documentation": [],
        "Other": [],
    }

    for mr in mrs:
        text = f"{mr.title} {mr.description or ''}".lower()
        if any(kw in text for kw in ["security", "vulnerability", "cve"]):
            buckets["Security"].append(mr)
        elif any(kw in text for kw in ["bug", "fix", "crash", "regression", "error"]):
            buckets["Bug Fixes"].append(mr)
        elif any(kw in text for kw in ["perf", "performance", "slow", "latency", "memory"]):
            buckets["Performance"].append(mr)
        elif any(kw in text for kw in ["ci", "cd", "pipeline", "deploy", "build"]):
            buckets["CI/CD"].append(mr)
        elif any(kw in text for kw in ["doc", "readme", "typo", "spelling"]):
            buckets["Documentation"].append(mr)
        elif any(kw in text for kw in ["feature", "add", "new", "implement", "support", "enhancement"]):
            buckets["Features"].append(mr)
        else:
            buckets["Other"].append(mr)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Release Notes — {project.name_with_namespace}",
        f"**Period:** {from_date[:10]} → {today}",
        f"**Total MRs:** {len(mrs)}\n",
    ]

    for section, section_mrs in buckets.items():
        if not section_mrs:
            continue
        lines.append(f"## {section}\n")
        for mr in section_mrs:
            merged_by = mr.merged_by["name"] if mr.merged_by else mr.author["name"]
            lines.append(f"- **{mr.title}** (!{mr.iid}) by @{mr.author['username']} — merged by {merged_by}")
            if mr.description:
                first_line = mr.description.strip().splitlines()[0][:120]
                lines.append(f"  _{first_line}_")
        lines.append("")

    return "\n".join(lines)


def close_issue(project_id: str, issue_iid: int) -> str:
    """Closes an open GitLab issue."""
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_iid)
    if issue.state == "closed":
        return f"Issue #{issue_iid} '{issue.title}' is already closed."
    issue.state_event = "close"
    issue.save()
    return f"Issue #{issue_iid} '{issue.title}' has been closed successfully."


def add_issue_comment(project_id: str, issue_iid: int, body: str) -> str:
    """Posts a comment on a GitLab issue."""
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_iid)
    note = issue.notes.create({"body": body})
    return f"Comment posted on #{issue_iid} '{issue.title}' (note ID: {note.id})."


def merge_merge_request(project_id: str, mr_iid: int) -> str:
    """Merges an open MR if it is in a mergeable state."""
    project = gl.projects.get(project_id)
    mr = project.mergerequests.get(mr_iid)
    if mr.state != "opened":
        return f"MR !{mr_iid} cannot be merged — current state is '{mr.state}'."
    if mr.merge_status != "can_be_merged":
        return (
            f"MR !{mr_iid} '{mr.title}' is not mergeable.\n"
            f"merge_status: {mr.merge_status} (conflicts, pending checks, or missing approvals)."
        )
    mr.merge()
    return f"MR !{mr_iid} '{mr.title}' has been merged into `{mr.target_branch}`."


def auto_triage_all_issues(project_id: str) -> str:
    """Scans all open issues and applies inferred labels and a priority comment to each."""
    project = gl.projects.get(project_id)
    issues = project.issues.list(state="opened", all=True, order_by="created_at", sort="asc")
    if not issues:
        return f"No open issues found in project {project_id}."

    results = []
    for issue in issues:
        text = f"{issue.title} {issue.description or ''}"
        priority = _infer_priority(text)
        suggested_labels = _infer_labels(text)
        new_labels = [l for l in suggested_labels if l not in issue.labels]

        if new_labels:
            issue.labels = issue.labels + new_labels
            issue.save()

        comment = (
            f"**Auto-triage**\n"
            f"- **Priority:** {priority.upper()}\n"
            f"- **Labels applied:** {', '.join(new_labels) if new_labels else 'none (already labelled)'}\n"
            f"_Inferred from title and description keywords by the GitLab DevOps agent._"
        )
        issue.notes.create({"body": comment})
        results.append(
            f"#{issue.iid} [{priority.upper()}] {issue.title} — new labels: {', '.join(new_labels) if new_labels else 'none'}"
        )

    return f"Auto-triaged {len(issues)} issue(s) in {project.name_with_namespace}:\n" + "\n".join(results)
