import datetime

from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tasks.models import STATUS_CHOICES, ReportConfig, Task

from tasks.views import TaskCreateForm, session_storage_view


class GenericTaskViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user)

    def test_list_with_unauthenticated_user(self):
        """
        Try to GET the tasks listing page with unauthenticated user, expect the response to redirect to the login page
        """
        response = self.client.get(reverse('tasks-view'), follow=False)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('tasks-view'))

    def test_list_with_authenticated_user(self):
        """
        Try to GET the tasks listing page with authenticated user, expect the response to list the tasks
        """
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.get(reverse('tasks-view'), follow=False)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks.html')

    def test_list_search_GET(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        search_term = 'abc'
        response = self.client.get(reverse('tasks-view'), {'search':search_term}, follow=True)
        self.assertQuerysetEqual(response.context['tasks'], Task.objects.filter(deleted = False, completed = False, user=self.user).order_by('priority').filter(title__icontains = search_term))
        self.assertEqual(response.status_code, 200)

class UserLoginViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.login_url = reverse('user-login')
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")

    def test_successful_authentication(self):
        """
        Try to login with correct credentials, expect the authentication to be successful
        """
        credentials = {
            'username':'bruce_wayne',
            'password':'i_am_batman'
        }
        response = self.client.post(self.login_url, credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

    def test_unsuccessful_authentication(self):
        """
        Try to login with incorrect credentials, expect the authentication to fail
        """
        credentials = {
            'username':'fasdfas',
            'password':'dsfsf'
        }
        response = self.client.post(self.login_url, credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


class session_storage_view_test(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")


    def test_session_storage_view(self):
        request = self.factory.get("sessiontest")
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        request.session.save()
        request.user = self.user
    
        response = session_storage_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total views is 0 and the user id is bruce_wayne')
        response = session_storage_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total views is 1 and the user id is bruce_wayne')

class GenericTaskDeleteViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")

    def test_GenericTaskDeleteView(self):
        """
        Try to delete user created task, expect the task to be soft deleted
        """
        self.client.login(username="bruce_wayne", password="i_am_batman")
        Task(title='test', user=self.user).save()
        Task(title='test2', user=self.user).save()
        self.assertEqual(Task.objects.filter(user=self.user, deleted=False).count(), 2)
        response = self.client.post(reverse('delete-task', kwargs={'pk':Task.objects.filter(user=self.user)[0].id}), follow=True)
        self.assertEqual(Task.objects.filter(user=self.user, deleted=False).count(), 1)

class TaskCreateFormTest(TestCase):
    def test_form_with_title_less_than_5(self):
        form_data = {'title':'abc','description':'test','priority':1,'status':'PENDING'}
        form = TaskCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
    def test_form_with_title_more_than_5(self):
        form_data = {'title':'abcdef','description':'test','priority':1,'status':'PENDING'}
        form = TaskCreateForm(data=form_data)
        self.assertTrue(form.is_valid())
        

class GenericTaskCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")

    def test_generic_task_create_with_unauthenticated_POST(self):
        response = self.client.post(reverse('create-task'), {'title':'abcdefg', 'description':'test', 'priority':1, 'status':STATUS_CHOICES[0][0]}, follow=False)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('create-task'))


    def test_generic_task_create_with_title_more_than_5_characters(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('create-task'), {'title':'abcdefg', 'description':'test', 'priority':1, 'status':STATUS_CHOICES[0][0]}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user, deleted=False).count(), 1)

    def test_generic_task_create_priority_cascade(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('create-task'), {'title':'abcdefg1', 'description':'test', 'priority':1, 'status':STATUS_CHOICES[0][0]}, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('create-task'), {'title':'abcdefg2', 'description':'test', 'priority':1, 'status':STATUS_CHOICES[0][0]}, follow=True)
        self.assertEqual(response.status_code, 200)
        task_one = Task.objects.filter(user=self.user, deleted=False, title__iexact='abcdefg1').first()
        task_two = Task.objects.filter(user=self.user, deleted=False, title__iexact='abcdefg2').first()
        self.assertEqual(task_two.priority, 1)
        self.assertEqual(task_one.priority, 2)
        

class GenericTaskUpdateViewTest(TestCase):
    def setUp(self):
            self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
            self.task_one = Task.objects.create(title='abcdefg1', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user)
            self.task_two = Task.objects.create(title='abcdefg2', description='test', priority=2, status = STATUS_CHOICES[0][0] , user=self.user)
            self.task_four = Task.objects.create(title='abcdefg4', description='test', priority=4, status = STATUS_CHOICES[0][0] , user=self.user)

    def test_generic_task_update_POST_unauthenticated(self):
        response = self.client.post(reverse('update-task', kwargs = {'pk':self.task_two.id}), {'title':'abcdefg2','description':'test','priority':1,'status':STATUS_CHOICES[0][0]}, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('update-task', kwargs = {'pk':self.task_two.id}))

    def test_generic_task_update_POST_priority_cascade(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('update-task', kwargs = {'pk':self.task_two.id}), {'title':'abcdefg2','description':'test','priority':1,'status':STATUS_CHOICES[0][0]}, follow=True)
        self.assertEqual(Task.objects.filter(id=self.task_one.id).first().priority, 2)
        self.assertEqual(Task.objects.filter(id=self.task_two.id).first().priority, 1)

    def test_generic_task_update_POST_priority_cascade_with_gap(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('update-task', kwargs = {'pk':self.task_two.id}), {'title':'abcdefg2','description':'test','priority':1,'status':STATUS_CHOICES[0][0]}, follow=True)
        self.assertEqual(Task.objects.filter(id=self.task_one.id).first().priority, 2)
        self.assertEqual(Task.objects.filter(id=self.task_two.id).first().priority, 1)
        self.assertEqual(Task.objects.filter(id=self.task_four.id).first().priority, 4)


class GenericAllTaskViewTest(TestCase):
    def setUp(self):
            self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
            self.task_one = Task.objects.create(title='abcdefg1', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user, completed = False)
            self.task_two = Task.objects.create(title='abcdefg2', description='test', priority=2, status = STATUS_CHOICES[0][0] , user=self.user, completed = True)
      
    def test_generic_list_all_tasks_GET_unauthenticated(self):
        response = self.client.get(reverse('all-tasks-view'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('all-tasks-view'))

    def test_generic_list_all_tasks_GET_authenticated(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.get(reverse('all-tasks-view'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['all_tasks'],Task.objects.filter(deleted = False, user = self.user).order_by('completed','priority'))

class GenericTaskCompleteListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg1', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user, completed = False)
        self.task_two = Task.objects.create(title='abcdefg2', description='test', priority=2, status = STATUS_CHOICES[0][0] , user=self.user, completed = True)
        self.task_three = Task.objects.create(title='abcdefg3', description='test', priority=3, status = STATUS_CHOICES[0][0] , user=self.user, completed = True)

    def test_generic_list_completed_tasks_GET_unauthenticated(self):
        response = self.client.get(reverse('complete-list'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('complete-list'))

    def test_generic_list_completed_tasks_GET_authenticated(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.get(reverse('complete-list'), follow=False)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['tasks'],Task.objects.filter(completed = True, deleted = False, user=self.user).order_by('priority'))

    
class GenericTaskCompleteUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        self.task_one = Task.objects.create(title='abcdefg1', description='test', priority=1, status = STATUS_CHOICES[0][0] , user=self.user, completed = False)
        self.task_two = Task.objects.create(title='abcdefg2', description='test', priority=2, status = STATUS_CHOICES[0][0] , user=self.user, completed = True)
    
    def test_generic_update_to_completed_task_unauthenticated_POST(self):
        response = self.client.post(reverse('complete-task', kwargs = {'pk':self.task_one.id}),follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('complete-task', kwargs = {'pk':self.task_one.id}))

    def test_generic_update_to_completed_task_authenticated_POST(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('complete-task', kwargs = {'pk':self.task_one.id}),follow=True)
        self.assertRedirects(response, reverse('tasks-view'))
        self.assertEqual(Task.objects.filter(completed=True, user=self.user).count(), 2)


class GenericReportUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
     
    def test_generic_report_config_add_unauthenticated_POST(self):
        response = self.client.post(reverse('create-report'),follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('user-login')+"?next="+reverse('create-report'))

    def test_generic_report_config_add_authenticated_POST(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('create-report'),{'time':datetime.time(9, 0)},follow=True)
        self.assertRedirects(response, reverse('tasks-view'))
        self.assertEqual(ReportConfig.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ReportConfig.objects.filter(user=self.user).first().time, datetime.time(9, 0))

    def test_generic_report_config_update_authenticated_POST(self):
        self.client.login(username="bruce_wayne", password="i_am_batman")
        response = self.client.post(reverse('create-report'),{'time':datetime.time(9, 0)},follow=True)
        self.assertRedirects(response, reverse('tasks-view'))
        self.assertEqual(ReportConfig.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ReportConfig.objects.filter(user=self.user).first().time, datetime.time(9, 0))
        response = self.client.post(reverse('create-report'),{'time':datetime.time(10, 0)},follow=True)
        self.assertRedirects(response, reverse('tasks-view'))
        self.assertEqual(ReportConfig.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ReportConfig.objects.filter(user=self.user).first().time, datetime.time(10, 0))
