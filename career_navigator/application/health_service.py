from career_navigator.domain.health import Health


class HealthService:
    def get_health(self) -> Health:
        return Health(status="ok")
