"""task_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers
from tasks.apiviews import TaskListAPI, TaskStatusHistoryViewSet, TaskViewSet
from tasks.views import (CreateTaskView, GenericAllTaskView,
                         GenericReportUpdateView,
                         GenericTaskCompleteListView,
                         GenericTaskCompleteUpdateView,
                         GenericTaskCompleteView, GenericTaskCreateView,
                         GenericTaskDeleteView, GenericTaskDetailView,
                         GenericTaskUpdateView, GenericTaskView, TaskView,
                         UserCreateView, UserLoginView, add_task_view,
                         all_tasks_view, complete_list_view,
                         complete_task_view, delete_task_view,
                         session_storage_view)

router = SimpleRouter()
router.register("api/task", TaskViewSet, 'api-task')

task_router = routers.NestedSimpleRouter(router, "api/task", lookup="task")
task_router.register("history", TaskStatusHistoryViewSet, 'api-task-status-history')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tasks/', GenericTaskView.as_view(), name="tasks-view"),
    path("add-task/", add_task_view, name='add-task'),
    path('delete-task/<pk>', GenericTaskDeleteView.as_view(), name='delete-task'),
    path('complete_task/<pk>/', GenericTaskCompleteUpdateView.as_view(), name='complete-task'),
    path('completed_tasks/', GenericTaskCompleteListView.as_view(), name='complete-list'),
    path('all_tasks/', GenericAllTaskView.as_view(), name="all-tasks-view"),
    path('create-task/', GenericTaskCreateView.as_view(), name='create-task'),
    path('update-task/<pk>', GenericTaskUpdateView.as_view(), name='update-task'),
    path('detail-task/<pk>', GenericTaskDetailView.as_view(), name='detail-task'),
    path('user/signup', UserCreateView.as_view(), name='user-signup'),
    path('user/login', UserLoginView.as_view(), name='user-login'),
    path('user/logout', LogoutView.as_view(), name = "user-logout"),
    path('sessiontest', session_storage_view),
    path('', RedirectView.as_view(url='tasks/')),
    path("__reload__/", include("django_browser_reload.urls")),
    path("taskapi", TaskListAPI.as_view()),
    path('create-report', GenericReportUpdateView.as_view(), name='create-report')
] + router.urls + task_router.urls
