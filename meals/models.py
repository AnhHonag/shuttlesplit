from django.db import models
from django.conf import settings
from decimal import Decimal


class MealExpense(models.Model):
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=200)
    date = models.DateField()
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Tiền cơm'

    @property
    def total_amount(self):
        return sum(p.amount for p in self.participants.all())

    def __str__(self):
        return f"{self.name} - {self.date}"


class MealParticipant(models.Model):
    meal = models.ForeignKey(MealExpense, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_participations')
    amount = models.DecimalField(max_digits=10, decimal_places=0, default=0)

    class Meta:
        unique_together = ('meal', 'user')
        verbose_name = 'Người tham gia bữa ăn'

    def __str__(self):
        return f"{self.user.get_display_name()} — {self.meal.name}: {self.amount:,.0f}đ"
