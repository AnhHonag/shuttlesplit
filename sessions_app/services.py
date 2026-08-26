from django.db import transaction
from decimal import Decimal
from .models import BadmintonSession, SessionParticipant, GuestParticipant
from wallet.services import deduct_for_session


@transaction.atomic
def create_session(group, date, location, court_fee, shuttle_fee, water_fee,
                   other_fee, other_fee_note, note, participant_ids, created_by,
                   guest_names=None):
    session = BadmintonSession.objects.create(
        group=group, date=date, location=location,
        court_fee=court_fee, shuttle_fee=shuttle_fee,
        water_fee=water_fee, other_fee=other_fee,
        other_fee_note=other_fee_note, note=note,
        created_by=created_by,
    )
    _assign_participants(session, participant_ids, guest_names or [], created_by)
    return session


@transaction.atomic
def update_session_participants(session, participant_ids, updated_by, guest_names=None):
    """Cập nhật danh sách tham gia & tính lại chi phí"""
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
            description=f"Hoàn tiền - cập nhật buổi {session.date}",
            session=session,
            created_by=updated_by,
        )
    session.participants.all().delete()
    session.guests.all().delete()
    _assign_participants(session, participant_ids, guest_names or [], updated_by)


def _assign_participants(session, participant_ids, guest_names, created_by):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    clean_guests = [n.strip() for n in guest_names if n.strip()]
    count = len(participant_ids) + len(clean_guests)
    if count == 0:
        return
    fee_per_person = (Decimal(str(session.total_fee)) / count).quantize(Decimal('1'))

    participants = User.objects.filter(pk__in=participant_ids)
    for user in participants:
        SessionParticipant.objects.create(
            session=session, user=user, amount_owed=fee_per_person
        )
        deduct_for_session(user, session.group, fee_per_person, session, created_by)

    for name in clean_guests:
        GuestParticipant.objects.create(
            session=session, name=name, amount_owed=fee_per_person
        )
