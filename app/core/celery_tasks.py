from celery import Celery
from app.modules.email.service import MailService
from asgiref.sync import async_to_sync

c_app = Celery()
c_app.config_from_object("app.core.config")

@c_app.task()
def send_email(recipients: list[str], subject: str, body: str):
    message = MailService.create_message(recipients=recipients, subject=subject, body=body)
    async_to_sync(MailService().mail.send_message)(message)
    print("Email sent")