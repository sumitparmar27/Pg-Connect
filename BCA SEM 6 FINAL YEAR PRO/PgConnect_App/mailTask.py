import threading
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage

def send_contact_us_email(name, email, subject, message):
    from_email = settings.EMAIL_HOST_USER
    to_email = ['chandeljaimin@gmail.com']

    html_content = f"""
    <html><body>
        <h2>New Contact Inquiry</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong><br>{message}</p>
    </body></html>
    """

    email_message = EmailMessage(
        subject=f"Contact Form: {subject}",
        body=html_content,
        from_email=from_email,
        to=to_email
    )
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)


import threading
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage


def send_contact_us_email(name, email, subject, message):
    from_email = settings.EMAIL_HOST_USER
    to_email = ['chandeljaimin@gmail.com']

    html_content = f"""
    <html><body>
        <h2>New Contact Inquiry</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong><br>{message}</p>
    </body></html>
    """

    email_message = EmailMessage(
        subject=f"Contact Form: {subject}",
        body=html_content,
        from_email=from_email,
        to=to_email
    )
    email_message.content_subtype = "html"
    email_message.send(fail_silently=False)


