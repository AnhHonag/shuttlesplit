from django.db import transaction
from decimal import Decimal
from .models import BadmintonSession, SessionParticipant, SessionAdvance
from wallet.services import deduct_for_session, record_advance, reverse_advance


@transaction.atomic
def create_session(group, date, location, court_fee, shuttle_fee, water_fee,
                   other_fee, other_fee_note, note, participant_ids, created_by,
                   advances=None):
    """advances = list of (user_id, amount)"""
    session = BadmintonSession.objects.create(
        group=group, date=date, location=location,
        court_fee=court_fee, shuttle_fee=shuttle_fee,
        water_fee=water_fee, other_fee=other_fee,
        other_fee_note=other_fee_note, note=note,
        created_by=created_by,
    )
    _record_advances(session, advances or [], created_by)
    _assign_participants(session, participant_ids, created_by)
    return session


@transaction.atomic
def update_session_participants(session, participant_ids, updated_by, advances=None):
    """Cập nhật danh sách tham gia & tính lại chi phí"""
    # Reverse existing advances
    for adv in session.advances.select_related('user').all():
        reverse_advance(adv.user, session.group, adv.amount, session, updated_by)
    session.advances.all().delete()

    # Refund existing member deductions
    for p in session.participants.all():
        from wallet.services import get_or_create_wallet
        wallet = get_or_create_wallet(p.user, session.group)
        wallet.balance += p.amount_owed
        wallet.total_spent -= p.amount_owed
        wallet.save()
        from wallet.models import WalletTransaction
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TYPE_REFUND,
            amount=p.amount_owed,
            balance_before=wallet.balance - p.amount_owed,
            balance_after=wallet.balance,
            description=f"Hoan tien - cap nhat buoi {session.date}",
            session=session,
            created_by=updated_by,
        )
    session.participants.all().delete()

    _record_advances(session, advances or [], updated_by)
    _assign_participants(session, participant_ids, updated_by)


def _record_advances(session, advances, created_by):
    """advances = list of (user_id, amount)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    for user_id, amount in advances:
        amount = Decimal(str(amount))
        if amount <= 0:
            continue
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            continue
        SessionAdvance.objects.create(session=session, user=user, amount=amount)
        record_advance(user, session.group, amount, session, created_by)


def _assign_participants(session, participant_ids, created_by):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    participants = User.objects.filter(pk__in=participant_ids)
    count = len(participant_ids)
    if count == 0:
        return
    fee_per_person = (Decimal(str(session.total_fee)) / count).quantize(Decimal('1'))

    for user in participants:
        SessionParticipant.objects.create(
            session=session, user=user, amount_owed=fee_per_person
        )
        deduct_for_session(user, session.group, fee_per_person, session, created_by)
