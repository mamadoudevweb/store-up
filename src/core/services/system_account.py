class SystemAccount:
    """A mock account with full permissions for system events and background tasks."""
    def has_permission(self, domain: str, entity: str, action: str) -> bool:
        return True
