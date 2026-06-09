from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from groups.models import Group, GroupMember
from .models import BadmintonSession, SessionParticipant
from .services import create_session, update_session_participants

User = get_user_model()


@login_required
def create_session_view(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk, owner=request.user)
    members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')

    if request.method == 'POST':
        date = request.POST.get('date')
        location = request.POST.get('location', '').strip()
        court_fee = int(request.POST.get('court_fee', 0) or 0)
        shuttle_fee = int(request.POST.get('shuttle_fee', 0) or 0)
        water_fee = int(request.POST.get('water_fee', 0) or 0)
        other_fee = int(request.POST.get('other_fee', 0) or 0)
        other_fee_note = request.POST.get('other_fee_note', '').strip()
        note = request.POST.get('note', '').strip()
        participant_ids = request.POST.getlist('participants')

        if not date:
            messages.error(request, 'Vui lòng chọn ngày chơi')
            return render(request, 'sessions_app/create_session.html', {'group': group, 'members': members})
        if not participant_ids:
            messages.error(request, 'Vui lòng chọn ít nhất 1 thành viên tham gia')
            return render(request, 'sessions_app/create_session.html', {'group': group, 'members': members})

        session = create_session(
            group=group, date=date, location=location,
            court_fee=court_fee, shuttle_fee=shuttle_fee,
            water_fee=water_fee, other_fee=other_fee,
            other_fee_note=other_fee_note, note=note,
            participant_ids=participant_ids, created_by=request.user
        )
        messages.success(request, f'Tạo buổi chơi thành công! Mỗi người đóng {session.fee_per_person:,.0f}đ')
        return redirect('session_detail', pk=session.pk)

    return render(request, 'sessions_app/create_session.html', {'group': group, 'members': members})


@login_required
def session_detail(request, pk):
    session = get_object_or_404(BadmintonSession, pk=pk)
    group = session.group
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = membership.is_host
    participants = list(session.participants.select_related('user').all())
    all_members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    my_participation = next((p for p in participants if p.user_id == request.user.pk), None)

    # Attach correct group wallet to each participant
    from wallet.models import Wallet
    wallets = {w.user_id: w for w in Wallet.objects.filter(
        group=group, user_id__in=[p.user_id for p in participants]
    )}
    for p in participants:
        p.group_wallet = wallets.get(p.user_id)

    return render(request, 'sessions_app/session_detail.html', {
        'session': session,
        'participants': participants,
        'all_members': all_members,
        'is_host': is_host,
        'my_participation': my_participation,
    })


@login_required
def edit_session(request, pk):
    session = get_object_or_404(BadmintonSession, pk=pk)
    group = session.group
    if group.owner != request.user:
        messages.error(request, 'Chỉ chủ nhóm mới được chỉnh sửa buổi chơi')
        return redirect('session_detail', pk=pk)
    all_members = GroupMember.objects.filter(group=group, is_active=True).select_related('user')
    current_participant_ids = list(session.participants.values_list('user_id', flat=True))

    if request.method == 'POST':
        session.date = request.POST.get('date', session.date)
        session.location = request.POST.get('location', '').strip()
        session.court_fee = int(request.POST.get('court_fee', 0) or 0)
        session.shuttle_fee = int(request.POST.get('shuttle_fee', 0) or 0)
        session.water_fee = int(request.POST.get('water_fee', 0) or 0)
        session.other_fee = int(request.POST.get('other_fee', 0) or 0)
        session.other_fee_note = request.POST.get('other_fee_note', '').strip()
        session.note = request.POST.get('note', '').strip()
        session.save()

        participant_ids = request.POST.getlist('participants')
        if participant_ids:
            update_session_participants(session, participant_ids, request.user)
        messages.success(request, 'Cập nhật buổi chơi thành công!')
        return redirect('session_detail', pk=pk)

    return render(request, 'sessions_app/edit_session.html', {
        'session': session,
        'all_members': all_members,
        'current_participant_ids': current_participant_ids,
    })


@login_required
def session_list(request, group_pk):
    """Tất cả buổi chơi của nhóm, nhóm theo tháng"""
    group = get_object_or_404(Group, pk=group_pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = membership.is_host

    from itertools import groupby
    from decimal import Decimal

    all_sessions = list(
        BadmintonSession.objects.filter(group=group)
        .prefetch_related('participants')
        .order_by('-date', '-created_at')
    )
    for s in all_sessions:
        s.num_participants = len(s.participants.all())
        s.fpp = (s.total_fee / s.num_participants).quantize(Decimal('1')) if s.num_participants else Decimal('0')

    years = sorted({s.date.year for s in all_sessions}, reverse=True)

    selected_year = None
    try:
        y = int(request.GET.get('year', ''))
        if y in years:
            selected_year = y
    except (ValueError, TypeError):
        pass
    if not selected_year and years:
        selected_year = years[0]

    filtered = [s for s in all_sessions if not selected_year or s.date.year == selected_year]

    VI_MONTHS = ['', 'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5',
                 'Tháng 6', 'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12']

    monthly_data = []
    for (yr, mo), grp in groupby(filtered, key=lambda s: (s.date.year, s.date.month)):
        ms = list(grp)
        monthly_data.append({
            'label': f"{VI_MONTHS[mo]} năm {yr}",
            'month': mo,
            'year': yr,
            'sessions': ms,
            'count': len(ms),
            'total_fee': sum(s.total_fee for s in ms),
            'total_participants': sum(s.num_participants for s in ms),
        })

    year_total_sessions = sum(m['count'] for m in monthly_data)
    year_total_fee = sum(m['total_fee'] for m in monthly_data)

    return render(request, 'sessions_app/session_list.html', {
        'group': group,
        'is_host': is_host,
        'monthly_data': monthly_data,
        'years': years,
        'selected_year': selected_year,
        'year_total_sessions': year_total_sessions,
        'year_total_fee': year_total_fee,
    })


@login_required
def my_sessions(request):
    """Lịch sử tham gia của thành viên"""
    from wallet.models import Wallet
    from collections import defaultdict
    from decimal import Decimal

    # Fetch ordered oldest-first per group for FIFO computation
    participations = list(
        request.user.session_participations
        .select_related('session', 'session__group')
        .order_by('session__group_id', 'session__date', 'session__created_at')
    )

    wallets = {w.group_id: w for w in Wallet.objects.filter(user=request.user)}

    # FIFO: accumulate cost per group, paid if covered by total_deposited
    group_cumulative = defaultdict(Decimal)
    for p in participations:
        gid = p.session.group_id
        group_cumulative[gid] += p.amount_owed
        deposited = wallets[gid].total_deposited if gid in wallets else Decimal('0')
        p.is_paid = group_cumulative[gid] <= deposited

    # Re-sort newest first for display
    participations.sort(key=lambda p: (p.session.date, p.session.created_at), reverse=True)

    paid_count = sum(1 for p in participations if p.is_paid)
    unpaid_count = len(participations) - paid_count
    total_owed = sum(p.amount_owed for p in participations)
    unpaid_amount = sum(p.amount_owed for p in participations if not p.is_paid)

    return render(request, 'sessions_app/my_sessions.html', {
        'participations': participations,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'total_owed': total_owed,
        'unpaid_amount': unpaid_amount,
    })
