---
name: canary-deploy
description: Deploy a pre-built container image to Cloud Run using canary traffic splitting, monitor error rate via the Cloud Monitoring MCP server, and promote or rollback automatically.
---

# Skill: Canary Deploy to Cloud Run

## Trigger
Called with a merged PR URL, a pre-built container image, and GCP credentials.

## Tools available
- bash: gcloud CLI is pre-installed. Authenticate using the access token from the prompt.
- GitHub MCP server: read PR details, post issue comments, close issues.
- Cloud Monitoring MCP server: query Cloud Run metrics for the promote/rollback decision.
- Cloud Logging MCP server: read error log entries for rollback diagnosis only.

## Steps

<!-- TODO: Write the canary deploy workflow. The agent needs to know:
     1. How to authenticate gcloud using the token from the prompt
     2. How to record the current stable revision (critical - rollback needs this)
     3. How to deploy the new image with --no-traffic
     4. How to get the new revision name
     5. How to split traffic: 10% to new, 90% to stable
     6. The monitoring loop: 5 checks, 60 seconds apart, using Cloud Monitoring MCP
        - What metric to query (request_count, grouped by response_code_class)
        - How to compute canary_error_rate and stable_error_rate
        - The verdict table:
            canary_total < 5           -> HOLD
            error_rate > 5% AND > 2x stable -> ROLLBACK
            error_rate <= 5%           -> OK
            two consecutive HOLDs      -> ROLLBACK
     7. Promote path: --to-latest (keeps service in automatic mode)
     8. Rollback path: --to-revisions STABLE_REV=100
     9. How to get the service URL after the decision
    10. How to find the linked issue number from the PR body (look for "Closes #N")
    11. What to post on success (revision name + live URL, then close issue)
    12. What to post on rollback (error rate + log entries from Cloud Logging MCP)
-->
1. **Authenticate gcloud** using the access token from the prompt:
   ```bash
   export CLOUDSDK_AUTH_ACCESS_TOKEN=<token_from_prompt>
   ```

2. **Record the stable revision** before any change:
   ```bash
   gcloud run revisions list --service <SERVICE> --region <REGION> --project <PROJECT> \
     --format="value(REVISION)" --limit=1
   ```
   Save this as STABLE_REV. This is the rollback target.

3. **Deploy the new image with no traffic**:
   ```bash
   gcloud run deploy <SERVICE> \
     --image <IMAGE_URL> \
     --region <REGION> --project <PROJECT> \
     --no-traffic --quiet
   ```

4. **Get the new revision name**:
   ```bash
   gcloud run revisions list --service <SERVICE> --region <REGION> --project <PROJECT> \
     --format="value(REVISION)" --limit=1
   ```
   Save this as NEW_REV.

5. **Split traffic at 10%**:
   ```bash
   gcloud run services update-traffic <SERVICE> \
     --region <REGION> --project <PROJECT> \
     --to-revisions NEW_REV=10,STABLE_REV=90
   ```

6. **Monitoring loop** - run 5 checks, 60 seconds apart, using Cloud Monitoring MCP:
   - Query `run.googleapis.com/request_count` for the last 2 minutes, grouped by `response_code_class`
   - Compute canary_error_rate and stable_error_rate from 5xx vs total
   - Apply the verdict table:

   | Condition | Verdict |
   |---|---|
   | canary_total < 5 | HOLD |
   | canary_error_rate > 0.05 AND > stable_error_rate * 2 | ROLLBACK |
   | canary_error_rate <= 0.05 | OK |
   | Two consecutive HOLDs | ROLLBACK |

   Stop immediately on ROLLBACK. Proceed to step 7 after all 5 checks pass as OK.

7. **Promote** (all checks OK):
   ```bash
   gcloud run services update-traffic <SERVICE> --region <REGION> --project <PROJECT> --to-latest
   ```

   **Or rollback** (any ROLLBACK verdict):
   ```bash
   gcloud run services update-traffic <SERVICE> --region <REGION> --project <PROJECT> \
     --to-revisions STABLE_REV=100
   ```

8. **Get the service URL**:
   ```bash
   gcloud run services describe <SERVICE> --region <REGION> --project <PROJECT> \
     --format="value(status.url)"
   ```

9. **Find the linked issue number** from the PR body: look for "Closes #N" or "Fixes #N".

10. **On success**: post a comment on the issue with the revision name and live URL, then close the issue via GitHub MCP.

11. **On rollback**: use Cloud Logging MCP to fetch the top 5 recent error log entries for the service.
    Post a comment on the issue with the error rate, rollback reason, and log entries. Do NOT close the issue.

12. If no linked issue is found, skip GitHub steps - the deployment result is complete.
## Critical rules

<!-- TODO: Add the constraints that prevent dangerous deployment patterns.
     Cover: the logging vs monitoring distinction, recording stable rev, issue state on rollback.
-->
- **Always record STABLE_REV before step 3.** Rollback is impossible without it.
- **Never use Cloud Logging for the promote/rollback decision.** Use Cloud Monitoring MCP only.
- **Never close the issue on rollback.** The fix did not reach production.