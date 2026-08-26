from django.db import models
from django.conf import settings
from decimal import Decimal


class BadmintonSession(models.Model):
    STATUS_OPEN = 'open'
    STATUS_SETTLED = 'settled'
    STATUSES = [(STATUS_OPEN, 'Đang mở'), (STATUS_SETTLED, 'Đã quyết toán')]

    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    court_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    shuttle_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    water_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    other_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    other_fee_note = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=STATUS_OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Buổi chơi'
        ordering = ['-date', '-created_at']

    @property
    def total_fee(self):
        return self.court_fee + self.shuttle_fee + self.water_fee + self.other_fee

    @property
    def participant_count(self):
        return self.participants.count() + self.guests.count()

    @property
    def fee_per_person(self):
        count = self.participant_count
        if count == 0:
            return Decimal('0')
        return (Decimal(str(self.total_fee)) / count).quantize(Decimal('1'))

    def __str__(self):
        return f"{self.group.name} - {self.date}"


class SessionParticipant(models.Model):
    session = models.ForeignKey(BadmintonSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_participations')
    amount_owed = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'user')
        verbose_name = 'Người tham gia'

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.session}"


class GuestParticipant(models.Model):
    session = models.ForeignKey(BadmintonSession, on_delete=models.CASCADE, related_name='guests')
    name = models.CharField(max_length=100)
    amount_owed = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    is_paid = models.BooleanField(default=False)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Khách vãng lai'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} (vãng lai) - {self.session}"
