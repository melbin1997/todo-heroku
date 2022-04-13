from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from tasks.models import STATUS_CHOICES, Task


class TaskViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user)
    
    def test_api_task_list_unauthenticated_GET(self):
        response = self.client.get(reverse('api-task-list'), follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_task_list_authenticated_GET(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.get(reverse('api-task-list'), follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        

class TaskStatusHistoryViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user)
    
    def test_api_task_status_history_list_unauthenticated_GET(self):
        task = Task.objects.filter(id = self.task_one.id).first()
        task.status = STATUS_CHOICES[1][0]
        task.save()
        response = self.client.get(reverse('api-task-status-history-list', kwargs = {'task_pk':self.task_one.id}), follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_task_status_history_list_authenticated_GET(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        task = Task.objects.filter(id = self.task_one.id).first()
        task.status = STATUS_CHOICES[1][0]
        task.save()
        response = self.client.get(reverse('api-task-status-history-list', kwargs = {'task_pk':self.task_one.id}), follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        