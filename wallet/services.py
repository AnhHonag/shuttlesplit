from decimal import Decimal
from django.db import transaction
from .models import Wallet, WalletTransaction


def get_or_create_wallet(user, group):
    from django.db import IntegrityError
    try:
        return Wallet.objects.get(user=user, group=group)
    except Wallet.DoesNotExist:
        pass
    try:
        with transaction.atomic():
            return Wallet.objects.create(user=user, group=group)
    except IntegrityError:
        return Wallet.objects.get(user=user, group=group)


@transaction.atomic
def deposit(user, group, amount, description, created_by):
    """Nạp tiền vào ví"""
    wallet = get_or_create_wallet(user, group)
    amount = Decimal(str(amount))
    balance_before = wallet.balance

    wallet.balance += amount
    wallet.total_deposited += amount
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TYPE_DEPOSIT,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=description,
        created_by=created_by,
    )
    return wallet


@transaction.atomic
def deduct_for_session(user, group, amount, session, created_by):
    """Trừ tiền cho buổi chơi"""
    wallet = get_or_create_wallet(user, group)
    amount = Decimal(str(amount))
    balance_before = wallet.balance

    wallet.balance -= amount
    wallet.total_spent += amount
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TYPE_DEDUCT,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=f"Buổi chơi ngày {session.date} - {session.location or session.group.name}",
        session=session,
        created_by=created_by,
    )

    from django.conf import settings
    threshold = Decimal(str(getattr(settings, 'DEBT_REMINDER_THRESHOLD', 200000)))
    if wallet.debt >= threshold:
        wallet_id, group_id = wallet.id, group.id
        transaction.on_commit(lambda: _send_debt_reminder_after_deduct(wallet_id, group_id))

    return wallet


def _send_debt_reminder_after_deduct(wallet_id, group_id):
    try:
        from .models import Wallet
        from groups.models import Group
        from notifications.tasks import send_debt_reminder_email
        wallet = Wallet.objects.get(id=wallet_id)
        group = Group.objects.get(id=group_id)
        send_debt_reminder_email(wallet, group)
    except Exception as e:
        print(f"Auto debt reminder error: {e}")


@transaction.atomic
def confirm_payment(user, group, amount, payment, confirmed_by):
    """Xác nhận thanh toán công nợ"""
    wallet = get_or_create_wallet(user, group)
    amount = Decimal(str(amount))
    balance_before = wallet.balance

    wallet.balance += amount
    wallet.total_deposited += amount
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TYPE_DEBT_PAID,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=f"Thanh toán công nợ - xác nhận bởi {confirmed_by.get_display_name()}",
        payment=payment,
        created_by=confirmed_by,
    )
    return wallet


@transaction.atomic
def deduct_for_meal(user, group, amount, meal, created_by):
    """Trừ tiền cho bữa ăn (tiền cơm)"""
    wallet = get_or_create_wallet(user, group)
    amount = Decimal(str(amount))
    balance_before = wallet.balance

    wallet.balance -= amount
    wallet.total_spent += amount
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TYPE_MEAL,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=f"Tiền cơm: {meal.name} ({meal.date})",
        created_by=created_by,
    )
    return wallet


@transaction.atomic
def refund_for_meal(user, group, amount, meal_name, created_by):
    """Hoàn tiền khi xóa bữa ăn"""
    wallet = get_or_create_wallet(user, group)
    amount = Decimal(str(amount))
    balance_before = wallet.balance

    wallet.balance += amount
    wallet.total_spent = max(Decimal('0'), wallet.total_spent - amount)
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=WalletTransaction.TYPE_REFUND,
        amount=amount,
        balance_before=balance_before,
        balance_after=wallet.balance,
        description=f"Hoàn tiền cơm: {meal_name}",
        created_by=created_by,
    )
    return wallet


@transaction.atomic
def adjust_deposit(tx, new_amount, corrected_by, note=''):
    """Sửa lại số tiền nạp/trả nợ sai. Chỉ dùng cho TYPE_DEPOSIT và TYPE_DEBT_PAID."""
    new_amount = Decimal(str(new_amount))
    old_amount = tx.amount
    delta = new_amount - old_amount

    wallet = tx.wallet
    wallet.balance += delta
    wallet.total_deposited += delta
    wallet.save()

    if note:
        tx.description = note
    else:
        base = tx.description.split(' [Sửa')[0]
        tx.description = (
            f"{base} [Sửa: {old_amount:,.0f}đ → {new_amount:,.0f}đ"
            f" bởi {corrected_by.get_display_name()}]"
        )
    tx.amount = new_amount
    tx.balance_after = tx.balance_before + new_amount
    tx.save()
    return wallet, old_amount


def get_wallet_summary(user, group):
    wallet = get_or_create_wallet(user, group)
    return {
        'balance': wallet.balance,
        'total_deposited': wallet.total_deposited,
        'total_spent': wallet.total_spent,
        'debt': wallet.debt,
        'available': wallet.available_balance,
    }
