from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from groups.models import Group, GroupMember
from .models import Wallet, WalletTransaction
from .services import get_or_create_wallet


@login_required
def wallet_detail(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    wallet = get_or_create_wallet(request.user, group)
    transactions = wallet.transactions.all()[:30]
    return render(request, 'wallet/wallet_detail.html', {
        'group': group, 'wallet': wallet, 'transactions': transactions
    })
