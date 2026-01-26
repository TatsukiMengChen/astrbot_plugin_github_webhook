"""Push event handler."""

from astrbot.api import logger

from ..formatters.push_formatter import format_push_message


async def handle_push_event(data: dict, context):
    """Handle push event from GitHub webhook."""
    try:
        pusher = data.get("pusher", {})
        author_name = pusher.get("name", "Unknown")
        author_login = pusher.get("email", "")

        repository = data.get("repository", {})
        repo_name = repository.get("full_name", "Unknown")

        ref = data.get("ref", "")
        branch = ref.replace("refs/heads/", "") if ref else "Unknown"

        commits = data.get("commits", [])
        if not commits:
            logger.warning("GitHub Webhook: Push event has no commits")
            return None

        commit = commits[0]
        commit_message = commit.get("message", "No message")
        commit_url = commit.get("url", "")
        commit_id = commit.get("id", "")[:7]

        message = format_push_message(
            author_name=author_name,
            repo_name=repo_name,
            branch=branch,
            commit_message=commit_message,
            commit_url=commit_url,
            commit_id=commit_id,
        )

        return message

    except Exception as e:
        logger.error(f"GitHub Webhook: Error handling push event: {e}")
        return None
