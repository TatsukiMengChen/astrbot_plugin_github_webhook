"""GitHub Webhook Plugin constants."""

# Default port for webhook server
DEFAULT_PORT = 8080

# Default rate limit (requests per minute)
DEFAULT_RATE_LIMIT = 10

# Default LLM timeout (seconds)
DEFAULT_LLM_TIMEOUT = 60

# GitHub event types
EVENT_TYPE_PUSH = "push"
EVENT_TYPE_ISSUES = "issues"
EVENT_TYPE_PULL_REQUEST = "pull_request"
EVENT_TYPE_PING = "ping"

# Issue actions
ACTION_OPENED = "opened"
ACTION_CLOSED = "closed"
ACTION_REOPENED = "reopened"

# PR actions
ACTION_PR_OPENED = "opened"
ACTION_PR_CLOSED = "closed"
ACTION_PR_REOPENED = "reopened"
ACTION_PR_SYNCHRONIZED = "synchronized"
