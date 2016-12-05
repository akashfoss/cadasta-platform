from django.apps import AppConfig


class PartyConfig(AppConfig):
    name = 'party'
    verbose_name = 'Party'

    def ready(self):
        import party.signals
