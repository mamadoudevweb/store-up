class SystemAccount:
    """A mock account with full permissions for system events and background tasks."""
    def has_permission(self, domain: str, entity: str, action: str) -> bool:
        """
        Determine whether the account has permission to perform an action.
        
        Parameters:
            domain (str): The permission domain.
            entity (str): The target entity.
            action (str): The action to authorize.
        
        Returns:
            bool: `true` for every domain, entity, and action.
        """
        return True
