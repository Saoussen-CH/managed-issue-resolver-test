import os
import sys
from google import genai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
GH_TOKEN = os.environ["GH_TOKEN"]
REPO_URL = os.environ["REPO_URL"]
RESOLVER_AGENT_ID = os.environ["RESOLVER_AGENT_ID"]

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def resolve(issue_url: str):
    # TODO 1: Build the prompt
    # The agent needs two pieces of information to start:
    # - The GitHub issue URL (so it can read the issue via GitHub MCP)
    # - An authenticated clone URL (so it can git clone and git push)
    #
    # Build auth_repo_url by replacing "https://" with "https://x-access-token:{GH_TOKEN}@"
    # in REPO_URL. Then construct a prompt string with both values.
    #
    # auth_repo_url = ...
    # prompt = ...
    auth_repo_url = REPO_URL.replace("https://", f"https://x-access-token:{GH_TOKEN}@")

    prompt = (
        f"Resolve this GitHub issue: {issue_url}\n"
        f"Repository clone URL (authenticated): {auth_repo_url}\n\n"
        f"Use the GitHub MCP server to read the issue and open the PR. "
        f"Use the authenticated clone URL for git clone and git push."
    )
    # TODO 2: Call the Interactions API (data plane)
    # Use client.interactions.create() with:
    # - agent: the named agent ID (already defined above as RESOLVER_AGENT_ID)
    # - input: the prompt you built above
    # - tools: one MCP server entry for GitHub
    #     url: "https://api.githubcopilot.com/mcp/"
    #     name: "github"
    #     headers: Authorization Bearer token + X-MCP-Exclude-Tools: delete_file
    # - stream=True   (yield events to the log as the agent works)
    # - background=True  (return immediately; agent runs for minutes)
    # - store=True    (persist for potential multi-turn follow-up)
    #
    # Then iterate over the stream and print each event (truncated to 300 chars).
    print("TODO: implement the Interactions API call in resolve()", flush=True)
    stream = client.interactions.create(
        agent=RESOLVER_AGENT_ID,
        input=prompt,
        tools=[
            {
                "type": "mcp_server",
                "url": "https://api.githubcopilot.com/mcp/",
                "name": "github",
                "headers": {
                    "Authorization": f"Bearer {GH_TOKEN}",
                    "X-MCP-Exclude-Tools": "delete_file",
                },
            },
        ],
        stream=True,
        background=True,
        store=True,
    )

    for event in stream:
        print(str(event)[:300], flush=True)

    print("Agent completed.", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: resolve.py <issue_url>")
        sys.exit(1)
    resolve(sys.argv[1])
