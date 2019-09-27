from django import template
from stb_app import models

register = template.Library()


@register.inclusion_tag('stb_app/notification_icon.html')
def is_notify(user):
    notification = models.Notification.objects.filter(
        notifying=user,
        seen=False)
    if notification:
        to_notify = True
        count = notification.count()
    else:
        to_notify = False
        count = 0

    return {'to_notify': to_notify, 'count': count}


@register.simple_tag
def notify_clear(user):
    notifications = models.Notification.objects.filter(
        notifying=user,
        seen=False)
    notifications.update(seen=True)


@register.simple_tag
def applied(applications, user):
    user_list = []
    for application in applications:
        user_list.append(application.applicant)
    if user in user_list:
        return True
    else:
        return False