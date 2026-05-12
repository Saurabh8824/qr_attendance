from django.apps import AppConfig


class QrAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "qr_app"
    
    def ready(self):
        import qr_app.signals
        
    verbose_name = "QR Attendance System"


