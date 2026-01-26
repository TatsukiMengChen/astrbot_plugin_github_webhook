"""Pull request event handler."""

from astrbot.api import logger

from ..formatters.pull_request_formatter import format_pull_request_message


async def handle_pull_request_event(data: dict, context):
    """Handle pull request event from GitHub webhook."""
    try:
        action = data.get("action", "unknown")
        pull_request = data.get("pull_request", {})
        repository = data.get("repository", {})

        pr_number = pull_request.get("number", 0)
        title = pull_request.get("title", "No title")
        pr_url = pull_request.get("html_url", "")

        sender = data.get("sender", {})
        author_name = sender.get("login", "Unknown")

        repo_name = repository.get("full_name", "Unknown")

        base_branch = pull_request.get("base", {}).get("ref", "unknown")
        head_branch = pull_request.get("head", {}).get("ref", "unknown")

        message = format_pull_request_message(
            action=action,
            author_name=author_name,
            repo_name=repo_name,
            pr_number=pr_number,
            title=title,
            base_branch=base_branch,
            head_branch=head_branch,
            pr_url=pr_url,
        )

        return message

    except Exception as e:
        logger.error(f"GitHub Webhook: Error handling pull_request event: {e}")
        return None
