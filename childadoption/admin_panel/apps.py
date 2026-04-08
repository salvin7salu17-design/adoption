from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    name = 'admin_panel'

    def ready(self):
        # Ensure a default admin account exists for testing
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(username='admin', email='admin@example.com', password='admin123')
