"""Issues event handler."""

from astrbot.api import logger

from ..formatters.issues_formatter import format_issue_message


async def handle_issues_event(data: dict, context):
    """Handle issues event from GitHub webhook."""
    try:
        action = data.get("action", "unknown")
        issue = data.get("issue", {})
        repository = data.get("repository", {})

        issue_number = issue.get("number", 0)
        title = issue.get("title", "No title")
        body = issue.get("body", "")
        issue_url = issue.get("html_url", "")

        sender = data.get("sender", {})
        author_name = sender.get("login", "Unknown")

        repo_name = repository.get("full_name", "Unknown")

        message = format_issue_message(
            action=action,
            author_name=author_name,
            repo_name=repo_name,
            issue_number=issue_number,
            title=title,
            issue_url=issue_url,
        )

        return message

    except Exception as e:
        logger.error(f"GitHub Webhook: Error handling issues event: {e}")
        return None
