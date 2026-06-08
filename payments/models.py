from django.db import models
from django.conf import settings


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'
    STATUSES = [
        (STATUS_PENDING, 'Chờ xác nhận'),
        (STATUS_CONFIRMED, 'Đã xác nhận'),
        (STATUS_REJECTED, 'Từ chối'),
    ]

    METHOD_TRANSFER = 'transfer'
    METHOD_CASH = 'cash'
    METHODS = [(METHOD_TRANSFER, 'Chuyển khoản'), (METHOD_CASH, 'Tiền mặt')]

    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='payments')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_made')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    method = models.CharField(max_length=20, choices=METHODS, default=METHOD_TRANSFER)
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    note = models.TextField(blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='payments_confirmed'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thanh toán'

    def __str__(self):
        return f"{self.member.get_display_name()} - {self.amount:,.0f}đ - {self.get_status_display()}"
