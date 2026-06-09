from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from groups.models import Group, GroupMember
from wallet.services import confirm_payment, get_or_create_wallet
from .models import Payment
from notifications.tasks import send_payment_request_to_host, send_payment_confirmed_to_member


@login_required
def submit_payment(request, group_pk):
    """Thành viên gửi xác nhận đã chuyển khoản"""
    group = get_object_or_404(Group, pk=group_pk)
    get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    wallet = get_or_create_wallet(request.user, group)

    if request.method == 'POST':
        amount = int(request.POST.get('amount', 0) or 0)
        method = request.POST.get('method', Payment.METHOD_TRANSFER)
        note = request.POST.get('note', '').strip()

        if amount <= 0:
            messages.error(request, 'Số tiền phải lớn hơn 0')
            return render(request, 'payments/submit_payment.html', {'group': group, 'wallet': wallet})

        payment = Payment.objects.create(
            group=group, member=request.user,
            amount=amount, method=method, note=note,
        )

        if request.FILES.get('receipt_image'):
            payment.receipt_image = request.FILES['receipt_image']
            payment.save()

        send_payment_request_to_host(payment)
        messages.success(request, 'Đã gửi thông báo cho chủ nhóm. Chờ xác nhận!')
        return redirect('group_detail', pk=group_pk)

    return render(request, 'payments/submit_payment.html', {'group': group, 'wallet': wallet})


@login_required
def payment_list(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = membership.is_host

    if is_host:
        payments = Payment.objects.filter(group=group).select_related('member')
    else:
        payments = Payment.objects.filter(group=group, member=request.user)

    return render(request, 'payments/payment_list.html', {
        'group': group,
        'payments': payments,
        'is_host': is_host,
    })


@login_required
def confirm_payment_view(request, payment_pk):
    """Chủ nhóm xác nhận thanh toán"""
    payment = get_object_or_404(Payment, pk=payment_pk)
    group = payment.group
    if group.owner != request.user:
        messages.error(request, 'Chỉ chủ nhóm mới được xác nhận thanh toán')
        return redirect('payment_list', group_pk=group.pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            payment.status = Payment.STATUS_CONFIRMED
            payment.confirmed_by = request.user
            payment.confirmed_at = timezone.now()
            payment.save()
            # Update wallet
            confirm_payment(payment.member, group, payment.amount, payment, request.user)
            send_payment_confirmed_to_member(payment)
            messages.success(request, f'Đã xác nhận thanh toán {payment.amount:,.0f}đ của {payment.member.get_display_name()}')
        elif action == 'reject':
            payment.status = Payment.STATUS_REJECTED
            payment.save()
            messages.warning(request, 'Đã từ chối thanh toán')

    return redirect('payment_list', group_pk=group.pk)


@login_required
def my_payments(request):
    """Lịch sử nộp tiền và giao dịch ví của thành viên"""
    from wallet.models import WalletTransaction, Wallet
    from django.db.models import Sum

    payments = list(
        Payment.objects.filter(member=request.user)
        .select_related('group', 'confirmed_by')
        .order_by('-created_at')
    )
    transactions = list(
        WalletTransaction.objects.filter(wallet__user=request.user)
        .select_related('wallet__group')
        .order_by('-created_at')
    )

    total_confirmed = sum(p.amount for p in payments if p.status == Payment.STATUS_CONFIRMED)
    pending_count = sum(1 for p in payments if p.status == Payment.STATUS_PENDING)

    total_balance = Wallet.objects.filter(user=request.user).aggregate(
        total=Sum('balance'))['total'] or 0

    return render(request, 'payments/my_payments.html', {
        'payments': payments,
        'transactions': transactions,
        'total_confirmed': total_confirmed,
        'pending_count': pending_count,
        'payments_count': len(payments),
        'transactions_count': len(transactions),
        'total_balance': total_balance,
    })


@login_required
def host_record_payment(request, group_pk, member_pk):
    """Chủ nhóm ghi nhận trực tiếp thành viên đã thanh toán"""
    group = get_object_or_404(Group, pk=group_pk, owner=request.user)
    membership = get_object_or_404(GroupMember, pk=member_pk, group=group, is_active=True)
    member_user = membership.user
    wallet = get_or_create_wallet(member_user, group)

    if request.method == 'POST':
        try:
            amount = int(request.POST.get('amount', 0) or 0)
        except ValueError:
            amount = 0
        method = request.POST.get('method', Payment.METHOD_CASH)
        note = request.POST.get('note', '').strip() or 'Ghi nhận bởi chủ nhóm'

        if amount <= 0:
            messages.error(request, 'Số tiền phải lớn hơn 0')
        elif amount > wallet.debt:
            messages.error(request, f'Số tiền ({amount:,}đ) lớn hơn công nợ hiện tại ({int(wallet.debt):,}đ)')
        else:
            payment = Payment.objects.create(
                group=group,
                member=member_user,
                amount=amount,
                method=method,
                note=note,
                status=Payment.STATUS_CONFIRMED,
                confirmed_by=request.user,
                confirmed_at=timezone.now(),
            )
            confirm_payment(member_user, group, amount, payment, request.user)
            messages.success(request, f'Đã ghi nhận {member_user.get_display_name()} thanh toán {amount:,}đ')
            return redirect('debt_report', pk=group_pk)

    return render(request, 'payments/record_payment.html', {
        'group': group,
        'membership': membership,
        'member': member_user,
        'wallet': wallet,
    })
