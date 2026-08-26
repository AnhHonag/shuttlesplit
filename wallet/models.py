from django.db import models
from django.conf import settings
from decimal import Decimal


class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='wallets')
    balance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_deposited = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'group')
        verbose_name = 'Ví tiền'

    @property
    def debt(self):
        return max(Decimal('0'), -self.balance)

    @property
    def available_balance(self):
        return max(Decimal('0'), self.balance)

    def __str__(self):
        return f"Ví {self.user.get_display_name()} - {self.group.name}: {self.balance:,.0f}đ"


class WalletTransaction(models.Model):
    TYPE_DEPOSIT = 'deposit'
    TYPE_DEDUCT = 'deduct'
    TYPE_DEBT_PAID = 'debt_paid'
    TYPE_REFUND = 'refund'
    TYPE_MEAL = 'meal'
    TYPE_ADVANCE = 'advance'
    TYPES = [
        (TYPE_DEPOSIT, 'Nạp tiền'),
        (TYPE_DEDUCT, 'Trừ tiền (buổi chơi)'),
        (TYPE_DEBT_PAID, 'Thanh toán nợ'),
        (TYPE_REFUND, 'Hoàn tiền'),
        (TYPE_MEAL, 'Tiền cơm'),
        (TYPE_ADVANCE, 'Ứng tiền buổi chơi'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    balance_before = models.DecimalField(max_digits=12, decimal_places=0)
    balance_after = models.DecimalField(max_digits=12, decimal_places=0)
    description = models.CharField(max_length=300, blank=True)
    session = models.ForeignKey('sessions_app.BadmintonSession', on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey('payments.Payment', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Giao dịch ví'

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount:,.0f}đ - {self.wallet.user.get_display_name()}"
