from django.apps import AppConfig


class OrganizationConfig(AppConfig):
    name = 'organization'
    verbose_name = 'Organization'

    def ready(self):
        import organization.signals
