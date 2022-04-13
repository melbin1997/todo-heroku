from django.contrib import admin

from tasks.models import Task, TaskStatusChange, ReportConfig, Notification


admin.sites.site.register(Task)
admin.sites.site.register(TaskStatusChange)
admin.sites.site.register(ReportConfig)
admin.sites.site.register(Notification)
