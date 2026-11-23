"""Static route diagnostics shared by the independent graph checks."""


class RouteBlocked(ValueError):
    """A selected route cannot execute at the identified graph instance."""

    def __init__(self, instance: str, reason: str):
        super().__init__(f'{reason} ({instance})')
        self.instance, self.reason = instance, reason
