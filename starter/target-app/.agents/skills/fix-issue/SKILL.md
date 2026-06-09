---
name: fix-issue
description: Clone a repository, diagnose a bug from a GitHub issue, fix it, and open a pull request.
---

# Skill: Fix GitHub Issue

## Trigger
Called with a GitHub issue URL and an authenticated repository clone URL.

## Tools available
- bash: git, pytest, pip, and standard Unix tools are pre-installed.
- GitHub MCP server: use it for all GitHub API operations (read issue, create PR, post comment).

## Workflow

<!-- TODO: Write the step-by-step workflow. The agent needs to know:
     1. How to read the issue (which tool, what information to extract)
     2. How to orient itself in the codebase before touching any files
     3. How to establish a failure baseline (what to run, what to record)
     4. How to diagnose from failing tests rather than guessing
     5. How to write the fix (scope: only the root cause)
     6. The quality gate before pushing (what must be true)
     7. How to create and push the branch and open the PR (naming convention, PR body)
-->
1. Read the issue using the GitHub MCP server to get the title, body, and number.

2. Clone the repository and read its structure:
   ```bash
   git clone <auth_repo_url> /workspace/repo
   cd /workspace/repo && ls -la
   ```

3. Install dependencies (check for `requirements.txt`, `package.json`, `pyproject.toml`).

4. Run the existing tests to see the current failure baseline.

5. Diagnose the issue using the symptom-to-location playbook.

6. Write the fix. Change only the code that causes the reported behavior.

7. Run the tests again. If any fail, iterate. Do not open a PR until all pass.

8. Commit and push:
   ```bash
   git config user.email "agent@managed-agents.dev"
   git config user.name "Issue Resolver Agent"
   git checkout -b fix/issue-<ISSUE_NUMBER>
   git add -A
   git commit -m "fix: <description> (closes #<ISSUE_NUMBER>)"
   git push origin fix/issue-<ISSUE_NUMBER>
   ```

9. Open a PR via GitHub MCP. Post a comment on the issue with the PR URL.
## Critical rules

<!-- TODO: Add the hard constraints from the skill's perspective.
     Focus on what must never be skipped (test run, specific tool for GitHub ops)
     and what must never happen (pushing with failing tests, creating new files).
-->
- **MANDATORY: run the full test suite before opening a PR.**
- **Do NOT create new files to apply a fix.**
- **Do NOT open a PR if any tests fail.** Iterate until they pass.