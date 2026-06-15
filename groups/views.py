from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Group, GroupMember
from wallet.models import Wallet
from wallet.services import get_or_create_wallet

User = get_user_model()


@login_required
def dashboard(request):
    user = request.user
    memberships = GroupMember.objects.filter(
        user=user, is_active=True, group__is_active=True
    ).select_related('group', 'group__owner')

    inactive_memberships = GroupMember.objects.filter(
        user=user, is_active=True, group__is_active=False, group__owner=user
    ).select_related('group')

    # Aggregate wallet data across active groups only
    active_group_ids = memberships.values_list('group_id', flat=True)
    wallets = Wallet.objects.filter(user=user, group_id__in=active_group_ids)
    total_balance = sum(w.balance for w in wallets)
    total_debt = sum(w.debt for w in wallets)

    from sessions_app.models import BadmintonSession
    recent_sessions = BadmintonSession.objects.filter(group_id__in=active_group_ids).order_by('-date')[:5]

    return render(request, 'groups/dashboard.html', {
        'memberships': memberships,
        'inactive_memberships': inactive_memberships,
        'total_balance': total_balance,
        'total_debt': total_debt,
        'recent_sessions': recent_sessions,
    })


@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        bank_name = request.POST.get('bank_name', '').strip()
        bank_bin = request.POST.get('bank_bin', '').strip()
        bank_account = request.POST.get('bank_account', '').strip()
        bank_owner = request.POST.get('bank_owner', '').strip()
        if not name:
            messages.error(request, 'Tên nhóm không được để trống')
            return render(request, 'groups/create_group.html')
        group = Group.objects.create(
            name=name, description=description, owner=request.user,
            bank_name=bank_name, bank_bin=bank_bin,
            bank_account=bank_account, bank_owner=bank_owner
        )
        GroupMember.objects.get_or_create(group=group, user=request.user, defaults={'role': GroupMember.ROLE_HOST})
        get_or_create_wallet(request.user, group)
        messages.success(request, f'Tạo nhóm "{name}" thành công!')
        return redirect('group_detail', pk=group.pk)
    return render(request, 'groups/create_group.html')


@login_required
def join_group(request):
    if request.method == 'POST':
        code = request.POST.get('invite_code', '').strip().upper()
        try:
            group = Group.objects.get(invite_code=code, is_active=True)
            _, created = GroupMember.objects.get_or_create(
                group=group, user=request.user,
                defaults={'role': GroupMember.ROLE_MEMBER}
            )
            if created:
                get_or_create_wallet(request.user, group)
                messages.success(request, f'Tham gia nhóm "{group.name}" thành công!')
            else:
                messages.info(request, f'Bạn đã là thành viên của nhóm "{group.name}"')
            return redirect('group_detail', pk=group.pk)
        except Group.DoesNotExist:
            messages.error(request, 'Mã mời không hợp lệ hoặc nhóm đã bị xóa')
    return render(request, 'groups/join_group.html')


@login_required
def group_detail(request, pk):
    from datetime import date
    from collections import defaultdict
    from sessions_app.models import SessionParticipant
    from django.db.models import Count

    group = get_object_or_404(Group, pk=pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = membership.is_host
    members = list(GroupMember.objects.filter(group=group, is_active=True).select_related('user'))

    # Batch-fetch wallets (1 query instead of N)
    user_ids = [m.user_id for m in members]
    existing_wallets = {w.user_id: w for w in Wallet.objects.filter(group=group, user_id__in=user_ids)}
    member_data = []
    for m in members:
        wallet = existing_wallets.get(m.user_id) or get_or_create_wallet(m.user, group)
        member_data.append({'member': m, 'wallet': wallet})

    my_wallet = existing_wallets.get(request.user.pk) or get_or_create_wallet(request.user, group)

    # Financial stats
    total_members = len(member_data)
    paid_count = sum(1 for d in member_data if d['wallet'].balance >= 0)
    debt_count = total_members - paid_count
    total_debt = sum(d['wallet'].debt for d in member_data)
    total_deposited = sum(d['wallet'].total_deposited for d in member_data)
    total_spent = sum(d['wallet'].total_spent for d in member_data)
    payment_rate = int(paid_count / total_members * 100) if total_members else 0

    # Sessions with per-session debt count (2 queries: sessions + prefetch participants)
    debtor_ids = {d['member'].user_id for d in member_data if d['wallet'].debt > 0}
    from decimal import Decimal
    sessions_list = list(group.sessions.prefetch_related('participants').order_by('-date', '-created_at')[:8])
    for s in sessions_list:
        parts = list(s.participants.all())
        s.total_participants = len(parts)
        s.debt_count = sum(1 for p in parts if p.user_id in debtor_ids)
        s.fpp = (s.total_fee / s.total_participants).quantize(Decimal('1')) if s.total_participants else Decimal('0')

    # Monthly costs last 6 months (1 query)
    today = date.today()
    start_mo, start_yr = today.month - 5, today.year
    while start_mo <= 0:
        start_mo += 12
        start_yr -= 1
    recent = list(group.sessions.filter(date__gte=date(start_yr, start_mo, 1)))
    mo_map = defaultdict(list)
    for s in recent:
        mo_map[(s.date.year, s.date.month)].append(s)

    monthly_costs = []
    for i in range(5, -1, -1):
        mo, yr = today.month - i, today.year
        while mo <= 0:
            mo += 12
            yr -= 1
        ss = mo_map.get((yr, mo), [])
        monthly_costs.append({
            'label': f'T{mo}',
            'cost': int(sum(s.total_fee for s in ss)),
            'count': len(ss),
            'is_current': (mo == today.month and yr == today.year),
        })
    max_monthly_cost = max((mc['cost'] for mc in monthly_costs), default=1) or 1
    six_month_total = sum(mc['cost'] for mc in monthly_costs)

    # Top participants by session count (2 queries)
    top_qs = list(
        SessionParticipant.objects.filter(session__group=group)
        .values('user_id').annotate(cnt=Count('id')).order_by('-cnt')[:5]
    )
    top_users = {u.pk: u for u in User.objects.filter(pk__in=[t['user_id'] for t in top_qs])}
    top_participants = [
        {'user': top_users[t['user_id']], 'cnt': t['cnt']}
        for t in top_qs if t['user_id'] in top_users
    ]

    return render(request, 'groups/group_detail.html', {
        'group': group, 'is_host': is_host,
        'members': members, 'member_data': member_data,
        'sessions': sessions_list, 'my_wallet': my_wallet,
        'total_debt': total_debt, 'total_deposited': total_deposited,
        'total_spent': total_spent, 'total_members': total_members,
        'paid_count': paid_count, 'debt_count': debt_count,
        'payment_rate': payment_rate, 'monthly_costs': monthly_costs,
        'max_monthly_cost': max_monthly_cost, 'six_month_total': six_month_total,
        'top_participants': top_participants,
        'total_sessions_count': group.sessions.count(),
    })


@login_required
def toggle_group_active(request, pk):
    group = get_object_or_404(Group, pk=pk, owner=request.user)
    if request.method == 'POST':
        group.is_active = not group.is_active
        group.save()
        status = 'đang hoạt động' if group.is_active else 'đã ngưng hoạt động'
        messages.success(request, f'Nhóm "{group.name}" {status}.')
    return redirect('group_detail', pk=pk)


@login_required
def group_settings(request, pk):
    group = get_object_or_404(Group, pk=pk, owner=request.user)
    if request.method == 'POST':
        group.name = request.POST.get('name', group.name).strip()
        group.description = request.POST.get('description', '').strip()
        group.bank_name = request.POST.get('bank_name', '').strip()
        group.bank_bin = request.POST.get('bank_bin', '').strip()
        group.bank_account = request.POST.get('bank_account', '').strip()
        group.bank_owner = request.POST.get('bank_owner', '').strip()
        group.is_active = request.POST.get('is_active') == '1'
        if request.FILES.get('cover_image'):
            group.cover_image = request.FILES['cover_image']
        elif request.POST.get('clear_cover'):
            group.cover_image = None
        if request.FILES.get('bank_qr'):
            group.bank_qr = request.FILES['bank_qr']
        elif request.POST.get('clear_bank_qr'):
            group.bank_qr = None
        group.save()
        status = 'đang hoạt động' if group.is_active else 'đã ngưng hoạt động'
        messages.success(request, f'Cập nhật nhóm thành công! Trạng thái: {status}.')
        return redirect('group_detail', pk=pk)
    return render(request, 'groups/group_settings.html', {'group': group})


@login_required
def add_member(request, pk):
    group = get_object_or_404(Group, pk=pk, owner=request.user)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Tên đăng nhập "{username}" đã được sử dụng')
        else:
            user = User.objects.create_user(
                username=username, password=password,
                full_name=full_name, email=email, phone=phone
            )
            if request.FILES.get('avatar'):
                user.avatar = request.FILES['avatar']
                user.save()
            GroupMember.objects.create(group=group, user=user, role=GroupMember.ROLE_MEMBER)
            get_or_create_wallet(user, group)
            messages.success(request, f'Thêm thành viên "{full_name}" thành công!')
            return redirect('group_detail', pk=pk)
    return render(request, 'groups/add_member.html', {'group': group})


@login_required
def edit_member(request, group_pk, member_pk):
    group = get_object_or_404(Group, pk=group_pk, owner=request.user)
    membership = get_object_or_404(GroupMember, pk=member_pk, group=group)
    user = membership.user
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        new_pass = request.POST.get('new_password', '').strip()
        if new_pass:
            user.set_password(new_pass)
        user.save()
        messages.success(request, 'Cập nhật thông tin thành viên thành công!')
        return redirect('group_detail', pk=group_pk)
    return render(request, 'groups/edit_member.html', {'group': group, 'membership': membership, 'member': user})


@login_required
def remove_member(request, group_pk, member_pk):
    group = get_object_or_404(Group, pk=group_pk, owner=request.user)
    membership = get_object_or_404(GroupMember, pk=member_pk, group=group)
    if membership.user == request.user:
        messages.error(request, 'Không thể xóa chính mình khỏi nhóm')
        return redirect('group_detail', pk=group_pk)
    if request.method == 'POST':
        membership.is_active = False
        membership.save()
        messages.success(request, f'Đã xóa {membership.user.get_display_name()} khỏi nhóm')
    return redirect('group_detail', pk=group_pk)


@login_required
def deposit_view(request, pk):
    """Chủ nhóm ghi nhận nạp tiền cho thành viên"""
    group = get_object_or_404(Group, pk=pk, owner=request.user)
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    if request.method == 'POST':
        from wallet.services import deposit
        user_id = request.POST.get('user_id')
        amount = request.POST.get('amount', 0)
        description = request.POST.get('description', 'Nạp tiền')
        try:
            target_user = User.objects.get(pk=user_id)
            wallet = deposit(target_user, group, int(amount), description, request.user)
            messages.success(request, f'Đã ghi nhận nạp {int(amount):,}đ cho {target_user.get_display_name()}')
            return redirect('group_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Lỗi: {e}')
    return render(request, 'groups/deposit.html', {'group': group, 'members': members})


@login_required
def send_debt_reminder(request, pk, member_pk):
    group = get_object_or_404(Group, pk=pk, owner=request.user)
    membership = get_object_or_404(GroupMember, pk=member_pk, group=group, is_active=True)
    next_url = request.POST.get('next') or request.GET.get('next') or 'debt_report'
    if request.method != 'POST':
        return redirect(next_url, pk=pk)
    user = membership.user
    wallet = get_or_create_wallet(user, group)

    if wallet.debt <= 0:
        messages.info(request, f'{user.get_display_name()} không có nợ.')
    elif not user.email:
        messages.warning(
            request,
            f'{user.get_display_name()} chưa có địa chỉ email — '
            f'hãy cập nhật email trong phần Chỉnh sửa thành viên.'
        )
    else:
        from notifications.tasks import send_debt_reminder_email
        sent = send_debt_reminder_email(wallet, group, force=True)
        if sent:
            messages.success(request, f'Đã gửi email nhắc nợ {wallet.debt:,.0f}đ đến {user.get_display_name()} ({user.email}).')
        else:
            from notifications.models import EmailNotification
            last_fail = EmailNotification.objects.filter(
                recipient=user,
                notification_type=EmailNotification.TYPE_DEBT_REMINDER,
                is_sent=False,
            ).order_by('-created_at').first()
            detail = f': {last_fail.error_message}' if last_fail and last_fail.error_message else ''
            messages.error(request, f'Gửi email thất bại{detail}. Kiểm tra cấu hình SMTP trong file .env.')
    return redirect(next_url, pk=pk)


@login_required
def debt_report(request, pk):
    """Báo cáo công nợ toàn nhóm"""
    group = get_object_or_404(Group, pk=pk)
    get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    
    member_data = []
    for m in members:
        wallet = get_or_create_wallet(m.user, group)
        recent_tx = wallet.transactions.all()[:5]
        member_data.append({
            'member': m,
            'wallet': wallet,
            'recent_transactions': recent_tx,
        })
    
    member_data.sort(key=lambda x: x['wallet'].balance)  # worst debt first
    
    return render(request, 'groups/debt_report.html', {
        'group': group,
        'member_data': member_data,
        'is_host': group.owner == request.user,
    })
