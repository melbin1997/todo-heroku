from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.views import View
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_filters.rest_framework import FilterSet, CharFilter, DjangoFilterBackend, ChoiceFilter, BooleanFilter, DateFilter

from .models import STATUS_CHOICES, Task, TaskStatusChange


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ("first_name","last_name","username")

class TaskSerializer(ModelSerializer):

    user = UserSerializer(read_only = True)

    class Meta:
        model = Task
        fields = ['id','title', 'description', 'completed','user', 'status']

class TaskFilter(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    status = ChoiceFilter(choices = STATUS_CHOICES)
    completed = BooleanFilter()

class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskFilter

    def get_queryset(self):
        return Task.objects.filter(user = self.request.user, deleted = False)

    def perform_create(self, serializer):
        serializer.save(user = self.request.user)


class TaskListAPI(APIView):
    def get(self,request):
        tasks = Task.objects.filter(deleted = False)
        data = TaskSerializer(tasks, many=True).data
        return Response({"tasks": data})

class TaskStatusFilter(FilterSet):
    new_status = ChoiceFilter(choices = STATUS_CHOICES)
    timestamp = DateFilter(lookup_expr="contains")

class TaskStatusSerializer(ModelSerializer):

    class Meta:
        model = TaskStatusChange
        read_only_fields =  ['old_status', 'new_status', 'timestamp']
        fields = ['old_status', 'new_status', 'timestamp']

class TaskStatusHistoryViewSet(ReadOnlyModelViewSet):
    queryset = TaskStatusChange.objects.all()
    serializer_class = TaskStatusSerializer

    permission_classes = [IsAuthenticated]

    filter_backends = (DjangoFilterBackend,)
    filterset_class = TaskStatusFilter

    def get_queryset(self):
        return TaskStatusChange.objects.filter(task = self.kwargs['task_pk'], task__user=self.request.user)
