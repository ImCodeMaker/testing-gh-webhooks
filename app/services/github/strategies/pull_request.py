import os
from typing import Any, Dict

from app.core.logger import logger
from app.services.github.strategies.base import GitHubEventStrategy
from app.services.notifications.discord import DiscordNotification
from app.services.github_client import GitHubClient
from app.services.ai.factory import get_ai_provider
from app.core.settings import settings


class PullRequestStrategy(GitHubEventStrategy):
    """Handles GitHub Pull Request events."""
    
    def __init__(self):
        self.discord = DiscordNotification()
        self.github_client = GitHubClient()
        
    async def execute(self, payload: Dict[str, Any]) -> None:
        action = payload.get("action", "unknown action")
        pr = payload.get("pull_request", {})
        number = pr.get("number", "unknown")
        title = pr.get("title", "No Title")
        pr_url = pr.get("html_url", "")
        author = pr.get("user", {}).get("login", "Unknown user")
        repo_name = payload.get("repository", {}).get("full_name", "Unknown Repo")
        repo_owner = payload.get("repository", {}).get("owner", {}).get("login", "Unknown")
        repo_short = payload.get("repository", {}).get("name", "Unknown")
        commit_sha = pr.get("head", {}).get("sha", "")
        
        logger.info(f"Processing PULL_REQUEST event: PR #{number} was {action}: {title}")
        
        # Configure color based on action
        color = 3447003 # Blue for open
        original_action = action
        if action == "closed":
            color = 15158332 if pr.get("merged") else 10038562 # Purple merged, Red closed
            if pr.get("merged"):
                action = "merged"

        role_id = os.getenv("DISCORD_ROLE_ID")
        # Execute the Template Method
        await self.discord.send_notification(
            title=f"🔀 Pull Request {action.capitalize()}",
            message = f"<@&{role_id}>\n**[{repo_name}]** PR #{number}: {title}\nAction by: {author}",
            metadata={
                "color": color,
                "author": author,
                "url": pr_url
            }
        )
        
        # --- AI CODE REVIEW PIPELINE ---
        
        # Proceed with AI Code Review only for open, sync, reopen
        if original_action not in ["opened", "synchronize", "reopened"]:
            return
            
        logger.info(f"Starting AI Code Review for PR #{number}")
        
        try:
            # Set commit status to pending so GitHub UI shows a loading state
            if commit_sha:
                await self.github_client.create_commit_status(
                    owner=repo_owner, 
                    repo=repo_short, 
                    sha=commit_sha, 
                    state="pending", 
                    description="AI is currently reviewing the code...", 
                    context="Chief AI / Code Review"
                )

            files = await self.github_client.get_pr_files(repo_owner, repo_short, number)
            
            ai_provider = get_ai_provider()
            provider_name = settings.AI_PROVIDER
            model_name = settings.AI_MODEL or "default"
            if model_name == "default":
                defaults = {
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "openai": "gpt-4o",
                    "gemini": "gemini-1.5-pro",
                    "groq": "llama-3.1-70b-versatile",
                    "ollama": "codellama"
                }
                model_name = defaults.get(provider_name, "default-model")
            
            reviews_text = []
            total_issues_found = 0
            
            # Aggregate severity counts for Discord embed
            severity_counts = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "SUGGESTION": 0
            }
            
            # We will default to APPROVE. If any file says REQUEST_CHANGES, we escalate the whole PR.
            final_verdict = "APPROVE"
            worst_score = 100
            
            import json
            import re
            
            for f in files:
                if f.status in ["removed", "unchanged"] or not f.patch:
                    continue
                    
                context = {
                    "repo": repo_name,
                    "title": title,
                    "filename": f.filename
                }
                
                raw_review_response = await ai_provider.review_code(f.patch, context)
                if not raw_review_response:
                    continue
                    
                # Clean potential markdown wrapping around JSON output before parsing
                json_str = re.sub(r'```json\n?(.*?)\n?```', r'\1', raw_review_response, flags=re.DOTALL).strip()
                try:
                    review_data = json.loads(json_str)
                    
                    file_verdict = review_data.get("verdict", "COMMENT")
                    if file_verdict == "REQUEST_CHANGES":
                        final_verdict = "REQUEST_CHANGES"
                    elif file_verdict == "COMMENT" and final_verdict == "APPROVE":
                        final_verdict = "COMMENT"
                        
                    file_score = review_data.get("score", 100)
                    if file_score < worst_score:
                        worst_score = file_score
                        
                    files_reviewed = review_data.get("files", [])
                    for file_item in files_reviewed:
                        issues = file_item.get("issues", [])
                        if not issues:
                            continue
                            
                        reviews_text.append(f"### File: `{f.filename}`\n")
                        for issue in issues:
                            severity = issue.get("severity", "LOW")
                            line = issue.get("line", "?")
                            issue_title = issue.get("title", "Issue")
                            desc = issue.get("description", "")
                            sugg = issue.get("suggestion", "")
                            
                            severity_counts[severity] = severity_counts.get(severity, 0) + 1
                            total_issues_found += 1
                            
                            reviews_text.append(f"**[{severity}] Line {line}: {issue_title}**\n{desc}")
                            if sugg:
                                reviews_text.append(f"\n*Suggestion:*\n```python\n{sugg}\n```")
                            reviews_text.append("\n---\n")
                
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse AI JSON response for {f.filename}. Raw Output: {raw_review_response[:100]}...")
                    continue
                    
            if not reviews_text:
                logger.info("No actionable feedback generated by AI. Skipping GitHub comment.")
                if commit_sha:
                    await self.github_client.create_commit_status(
                        owner=repo_owner, repo=repo_short, sha=commit_sha, 
                        state="success", description="AI review complete. No issues found.", context="Chief AI / Code Review"
                    )
                return
                
            summary_content = f"## 🤖 AI Code Review Summary\n\nReviewed by **{provider_name.capitalize()}** (`{model_name}`).\n\n**Verdict**: {final_verdict}\n**Score**: {worst_score}/100\n\n"
            full_review = summary_content + "\n".join(reviews_text)
            
            # Post review to GitHub using the aggregated VERDICT
            await self.github_client.post_pr_review(repo_owner, repo_short, number, full_review, event=final_verdict)
            
            if commit_sha:
                status_state = "failure" if final_verdict == "REQUEST_CHANGES" else "success"
                status_desc = f"Score: {worst_score}/100 | {total_issues_found} issues found"
                await self.github_client.create_commit_status(
                    owner=repo_owner, repo=repo_short, sha=commit_sha, 
                    state=status_state, description=status_desc, context="Chief AI / Code Review"
                )
            
            # Construct Discord notification mapping
            severity_breakdown = " | ".join([f"**{k}**: {v}" for k, v in severity_counts.items() if v > 0])
            embed_msg = (
                f"**Provider:** {provider_name.capitalize()} | **Model:** {model_name}\n"
                f"**Verdict:** {final_verdict} | **Score:** {worst_score}/100\n"
                f"**Total Issues:** {total_issues_found}\n\n"
                f"{severity_breakdown}"
            )
            
            embed_color = 3447003 # Default Blue Map
            if final_verdict == "REQUEST_CHANGES":
                embed_color = 10038562 # Red
            elif final_verdict == "APPROVE":
                embed_color = 3066993 # Green
                
            await self.discord.send_notification(
                title=f"🤖 AI Code Review Completed: PR #{number}",
                message=embed_msg,
                metadata={
                    "color": embed_color,
                    "author": author,
                    "url": pr_url
                }
            )
            
        except Exception as e:
            logger.error(f"Error during AI Code Review pipeline: {str(e)}", exc_info=True)
            if commit_sha:
                try:
                    await self.github_client.create_commit_status(
                        owner=repo_owner, repo=repo_short, sha=commit_sha, 
                        state="error", description="An error occurred during AI review.", context="Chief AI / Code Review"
                    )
                except Exception:
                    pass
            raise e
