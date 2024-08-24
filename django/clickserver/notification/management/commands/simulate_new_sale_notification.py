from django.core.management.base import BaseCommand
from notification.models import SaleNotificationSessions
from notification.views import NewSaleNotificationView
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Simulate a call to the NewSaleNotificationView using production data'

    def handle(self, *args, **kwargs):
        # Get the session you want to test with
        session_key = "your-session-key"  # Replace with an actual session key
        app_name = "your-app-name"  # Replace with an actual app name

        # Get the session object
        session = SaleNotificationSessions.objects.filter(session_key=session_key, app_name=app_name).first()

        if not session:
            self.stdout.write(self.style.ERROR(f"Session not found for key: {session_key} and app: {app_name}"))
            return

        # Simulate the request
        factory = RequestFactory()
        request = factory.get('/new_sale_notification/', {
            'token': session.user.token if session.user else '',
            'app_name': session.app_name,
            'session_id': session.session_key,
        })

        # Call the view
        view = NewSaleNotificationView.as_view()
        response = view(request)

        # Output the response
        self.stdout.write(self.style.SUCCESS(f"Response: {response.status_code}"))
        self.stdout.write(self.style.SUCCESS(f"Content: {response.content.decode('utf-8')}"))

