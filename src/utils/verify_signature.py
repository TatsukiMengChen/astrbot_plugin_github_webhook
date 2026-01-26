"""Webhook signature verification utilities."""

import hmac
import hashlib


def verify_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body bytes
        signature_header: X-Hub-Signature-256 header value
        secret: Webhook secret from GitHub

    Returns:
        True if signature is valid, False otherwise
    """
    if not secret or not signature_header:
        return False

    # GitHub signature format: sha256=...
    if not signature_header.startswith("sha256="):
        return False

    signature = signature_header[7:]  # Remove 'sha256=' prefix

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)
