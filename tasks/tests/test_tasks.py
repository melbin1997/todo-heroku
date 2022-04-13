import datetime
from datetime import datetime, timedelta

from celery.contrib.testing.worker import start_worker
from django.contrib.auth.models import User
from django.test import TestCase
from task_manager.celery import app
from tasks.models import STATUS_CHOICES, Notification, ReportConfig, Task
from tasks.tasks import send_task_summary


class TestCelery(TestCase):
    def setUp(self):
        start_worker(app)
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user)
        self.report_config = ReportConfig.objects.create(user = self.user, time = (datetime.now() - timedelta(hours=1)).time())

    def test_send_task_summary(self):
        result = send_task_summary.apply().get()
        self.assertIn(self.user.email, result)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)
