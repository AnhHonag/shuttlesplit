from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from groups.models import Group, GroupMember
from .models import Wallet, WalletTransaction
from .services import get_or_create_wallet


@login_required
def wallet_detail(request, group_pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    group = get_object_or_404(Group, pk=group_pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)

    # Host can view any member's wallet via ?user=<pk>
    target_user_pk = request.GET.get('user')
    if target_user_pk and membership.is_host:
        target_user = get_object_or_404(User, pk=target_user_pk)
        get_object_or_404(GroupMember, group=group, user=target_user, is_active=True)
        viewing_other = True
    else:
        target_user = request.user
        viewing_other = False

    wallet = get_or_create_wallet(target_user, group)
    transactions = wallet.transactions.all()[:50]

    from payments.models import Payment
    from django.db.models import Sum
    pending_qs = Payment.objects.filter(
        group=group, member=target_user, status=Payment.STATUS_PENDING
    )
    pending_amount = pending_qs.aggregate(total=Sum('amount'))['total'] or 0
    pending_count = pending_qs.count()

    return render(request, 'wallet/wallet_detail.html', {
        'group': group, 'wallet': wallet, 'transactions': transactions,
        'viewing_other': viewing_other, 'target_user': target_user,
        'pending_amount': pending_amount, 'pending_count': pending_count,
    })
