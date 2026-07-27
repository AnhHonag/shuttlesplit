from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
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
        'editable_types': [WalletTransaction.TYPE_DEPOSIT, WalletTransaction.TYPE_DEBT_PAID],
    })


@login_required
def edit_deposit(request, group_pk, tx_pk):
    """Chủ nhóm sửa lại số tiền nạp/trả nợ sai cho thành viên"""
    group = get_object_or_404(Group, pk=group_pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    if not membership.is_host:
        messages.error(request, 'Chỉ chủ nhóm mới có thể sửa giao dịch.')
        return redirect('wallet_detail', group_pk=group_pk)

    tx = get_object_or_404(
        WalletTransaction, pk=tx_pk, wallet__group=group,
        transaction_type__in=[WalletTransaction.TYPE_DEPOSIT, WalletTransaction.TYPE_DEBT_PAID],
    )
    wallet = tx.wallet
    member_user = wallet.user

    if request.method == 'POST':
        try:
            new_amount = int(request.POST.get('amount', 0) or 0)
        except (ValueError, TypeError):
            new_amount = 0
        note = request.POST.get('note', '').strip()

        if new_amount <= 0:
            messages.error(request, 'Số tiền phải lớn hơn 0.')
            return render(request, 'wallet/edit_deposit.html', {
                'group': group, 'tx': tx, 'wallet': wallet, 'member_user': member_user,
            })

        from .services import adjust_deposit
        old_amount = tx.amount
        adjust_deposit(tx, new_amount, request.user, note=note)
        messages.success(
            request,
            f'Đã sửa giao dịch cho {member_user.get_display_name()}: '
            f'{old_amount:,.0f}đ → {new_amount:,.0f}đ'
        )
        return redirect(
            reverse('wallet_detail', kwargs={'group_pk': group_pk})
            + f'?user={member_user.pk}'
        )

    return render(request, 'wallet/edit_deposit.html', {
        'group': group, 'tx': tx, 'wallet': wallet, 'member_user': member_user,
    })
