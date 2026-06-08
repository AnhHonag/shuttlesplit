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
    group = get_object_or_404(Group, pk=pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = membership.is_host
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    sessions = group.sessions.all()[:10]
    
    # Wallet summaries per member
    member_data = []
    for m in members:
        wallet = get_or_create_wallet(m.user, group)
        member_data.append({'member': m, 'wallet': wallet})

    my_wallet = get_or_create_wallet(request.user, group)

    return render(request, 'groups/group_detail.html', {
        'group': group,
        'is_host': is_host,
        'members': members,
        'member_data': member_data,
        'sessions': sessions,
        'my_wallet': my_wallet,
        'total_debt': sum(d['wallet'].debt for d in member_data),
    })


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
