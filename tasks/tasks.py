from datetime import timedelta, datetime
import time

from celery.decorators import periodic_task
from tasks.models import ReportConfig
from tasks.models import Task, Notification
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.db import transaction
from django.utils import timezone

from task_manager.celery import app

# @periodic_task(run_every=timedelta(seconds=10))
def send_email_reminder():
    print("Starting to process emails")
    for user in User.objects.all():
        pending_qs = Task.objects.filter(user=user, deleted=False, completed=False)
        email_content = f"You have {pending_qs.count()} pending tasks."
        send_mail("Pending Tasks from Task Manager", email_content, "tasks@taskmanager.com", [user.email])
        print(f'Completed email processing for user : {user.id}')

@periodic_task(run_every=timedelta(seconds=1))
def send_task_summary():
    currentTime = timezone.now()
    mail_sent_to = []

    for email_config in ReportConfig.objects.select_for_update().all():
        with transaction.atomic():
            if (email_config.last_sent_time == None or currentTime > email_config.last_sent_time + timedelta(days=1)) and currentTime.time() > email_config.time:
                qs = Task.objects.filter(user = email_config.user, deleted = False).values('status').annotate(total=Count('id')).order_by('status')
                email_content = f'Hi {email_config.user.username}\nPlease find the below task summary :\n'
                for task_summary in qs:
                    email_content += f"{task_summary.get('status')} : {task_summary.get('total')}\n"
                send_mail("Task Summary", email_content, "tasks@taskmanager.com", [email_config.user.email])
                mail_sent_to.append(email_config.user.email)
                Notification(user=email_config.user, content = email_content).save()
                email_config.last_sent_time = currentTime
                email_config.save(update_fields=['last_sent_time'])
                print(f'Completed task summary email for user : {email_config.user.username} for today with content : {email_content}')
    return mail_sent_to
