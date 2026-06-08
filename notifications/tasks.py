from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from django.template.loader import render_to_string
import datetime


def send_debt_reminder_email(wallet, group, force=False):
    """Gửi email nhắc nợ cho thành viên"""
    user = wallet.user
    if not user.email:
        return False

    if not force:
        from notifications.models import EmailNotification
        already_sent = EmailNotification.objects.filter(
            recipient=user,
            notification_type=EmailNotification.TYPE_DEBT_REMINDER,
            is_sent=True,
            sent_at__gte=timezone.now() - datetime.timedelta(hours=24),
        ).exists()
        if already_sent:
            return False

    debt = wallet.debt
    transfer_note = f"Thanh toan cau long - {user.get_display_name()}"

    subject = f"[ShuttleSplit] Nhắc thanh toán - {group.name}"
    body = f"""Xin chào {user.get_display_name()},

Bạn hiện đang nợ {debt:,.0f} VNĐ tiền cầu lông tại nhóm "{group.name}".

Vui lòng chuyển khoản theo thông tin bên dưới:

━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Ngân hàng: {group.bank_name or 'Liên hệ chủ nhóm'}
💳 Số tài khoản: {group.bank_account or 'Liên hệ chủ nhóm'}
👤 Chủ tài khoản: {group.bank_owner or group.owner.get_display_name()}
📝 Nội dung CK: {transfer_note}
💰 Số tiền: {debt:,.0f} VNĐ
━━━━━━━━━━━━━━━━━━━━━━━━

Sau khi chuyển khoản, vui lòng đăng nhập vào hệ thống để xác nhận thanh toán.

Trân trọng,
ShuttleSplit - {group.name}"""

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        from notifications.models import EmailNotification
        EmailNotification.objects.create(
            recipient=user,
            notification_type=EmailNotification.TYPE_DEBT_REMINDER,
            subject=subject, body=body, is_sent=True, sent_at=timezone.now()
        )
        return True
    except Exception as e:
        from notifications.models import EmailNotification
        EmailNotification.objects.create(
            recipient=user,
            notification_type=EmailNotification.TYPE_DEBT_REMINDER,
            subject=subject, body=body, is_sent=False, error_message=str(e)
        )
        return False


def send_payment_request_to_host(payment):
    """Thành viên bấm 'Đã chuyển khoản' -> email cho host"""
    group = payment.group
    host = group.owner
    if not host.email:
        return False

    member = payment.member
    subject = f"[ShuttleSplit] {member.get_display_name()} đã chuyển khoản {payment.amount:,.0f}đ"
    body = f"""Xin chào {host.get_display_name()},

Thành viên {member.get_display_name()} vừa thông báo đã chuyển khoản:

💰 Số tiền: {payment.amount:,.0f} VNĐ
📋 Phương thức: {payment.get_method_display()}
📝 Ghi chú: {payment.note or 'Không có'}

Vui lòng đăng nhập vào hệ thống để xác nhận thanh toán.

Trân trọng,
ShuttleSplit"""

    try:
        if payment.receipt_image:
            email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [host.email])
            email.attach_file(payment.receipt_image.path)
            email.send()
        else:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [host.email])
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_payment_confirmed_to_member(payment):
    """Host xác nhận -> email cho thành viên"""
    member = payment.member
    if not member.email:
        return False

    group = payment.group
    subject = f"[ShuttleSplit] Xác nhận nhận {payment.amount:,.0f}đ"
    body = f"""Xin chào {member.get_display_name()},

Chủ nhóm {group.owner.get_display_name()} đã xác nhận nhận được khoản thanh toán của bạn:

💰 Số tiền: {payment.amount:,.0f} VNĐ
✅ Trạng thái: Đã xác nhận

Số dư tài khoản của bạn đã được cập nhật.

Trân trọng,
ShuttleSplit - {group.name}"""

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [member.email])
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


# Celery task
def send_debt_reminders():
    """Celery beat task - chạy mỗi ngày"""
    from wallet.models import Wallet
    from decimal import Decimal
    threshold = Decimal(str(settings.DEBT_REMINDER_THRESHOLD))
    days_threshold = settings.DEBT_REMINDER_DAYS

    wallets_by_threshold = Wallet.objects.filter(balance__lt=-threshold)
    cutoff_date = timezone.now() - datetime.timedelta(days=days_threshold)
    wallets_by_age = Wallet.objects.filter(
        balance__lt=0,
        transactions__created_at__lte=cutoff_date,
        transactions__transaction_type='deduct'
    ).distinct()

    candidates = (wallets_by_threshold | wallets_by_age).distinct()
    sent = 0
    for wallet in candidates:
        if send_debt_reminder_email(wallet, wallet.group):
            sent += 1
    print(f"Sent {sent} debt reminder emails")
    return sent
