"""Integration domain package: outbox delivery and external boundary control."""
from .contracts import IntegrationSnapshot
from .policies import approval_required

__all__ = ["IntegrationSnapshot", "approval_required"]
