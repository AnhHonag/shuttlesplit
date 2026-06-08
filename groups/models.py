from django.db import models
from django.conf import settings
import random, string


def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_groups')
    invite_code = models.CharField(max_length=10, unique=True, default=gen_code)
    # Bank info for payment reminders
    bank_name = models.CharField(max_length=100, blank=True)
    bank_bin = models.CharField(max_length=20, blank=True)  # VietQR bank BIN code
    bank_account = models.CharField(max_length=50, blank=True)
    bank_owner = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Nhóm'

    def __str__(self):
        return self.name

    def get_active_members(self):
        return self.members.filter(is_active=True)


class GroupMember(models.Model):
    ROLE_HOST = 'host'
    ROLE_MEMBER = 'member'
    ROLES = [(ROLE_HOST, 'Chủ nhóm'), (ROLE_MEMBER, 'Thành viên')]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('group', 'user')
        verbose_name = 'Thành viên nhóm'

    def __str__(self):
        return f"{self.user.get_display_name()} - {self.group.name}"

    @property
    def is_host(self):
        return self.role == self.ROLE_HOST
