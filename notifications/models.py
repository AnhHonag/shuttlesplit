from django.db import models
from django.conf import settings


class EmailNotification(models.Model):
    TYPE_DEBT_REMINDER = 'debt_reminder'
    TYPE_PAYMENT_REQUEST = 'payment_request'
    TYPE_PAYMENT_CONFIRMED = 'payment_confirmed'
    TYPE_SESSION_CREATED = 'session_created'
    TYPES = [
        (TYPE_DEBT_REMINDER, 'Nhắc nợ'),
        (TYPE_PAYMENT_REQUEST, 'Yêu cầu thanh toán'),
        (TYPE_PAYMENT_CONFIRMED, 'Xác nhận thanh toán'),
        (TYPE_SESSION_CREATED, 'Buổi chơi mới'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPES)
    subject = models.CharField(max_length=300)
    body = models.TextField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thông báo email'
