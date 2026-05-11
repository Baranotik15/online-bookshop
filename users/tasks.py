import logging

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger('users')


@shared_task
def send_confirmation_email(user_pk, confirm_url):
    from users.models import User
    user = User.objects.get(pk=user_pk)
    body = render_to_string('users/email_confirm.html', {
        'user': user,
        'confirm_url': confirm_url,
    })
    try:
        send_mail(
            subject='Підтвердіть email — BookShop',
            message=body,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info('Confirmation email sent to %s (user_pk=%s)', user.email, user_pk)
    except Exception as e:
        logger.error('Failed to send confirmation email to %s: %s', user.email, str(e))
        raise
