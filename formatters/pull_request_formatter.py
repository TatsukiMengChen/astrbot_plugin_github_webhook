"""Pull request event formatter."""


def format_pull_request_message(
    action: str,
    author_name: str,
    repo_name: str,
    pr_number: int,
    title: str,
    base_branch: str,
    head_branch: str,
    pr_url: str,
) -> str:
    """Format pull request event message."""
    action_emoji = {
        "opened": "🆕",
        "closed": "✅",
        "reopened": "🔄",
        "synchronize": "🔀",
    }.get(action, "📝")

    return (
        f"{action_emoji} GitHub Pull Request Event\n"
        f"👤 {author_name} {action} PR in {repo_name}\n"
        f"📋 PR #{pr_number}: {title}\n"
        f"🌿 {head_branch} → {base_branch}\n"
        f"📎 {pr_url}"
    )
