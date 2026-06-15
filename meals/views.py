from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import date
from decimal import Decimal

from groups.models import Group, GroupMember
from wallet.services import get_or_create_wallet, deduct_for_meal, refund_for_meal
from .models import MealExpense, MealParticipant


@login_required
def create_meal(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    membership = get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    if not membership.is_host:
        messages.error(request, 'Chỉ chủ nhóm mới có thể tạo phiếu tiền cơm.')
        return redirect('group_detail', pk=group_pk)

    members = list(GroupMember.objects.filter(group=group, is_active=True).select_related('user'))

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        meal_date = request.POST.get('date', str(date.today()))
        note = request.POST.get('note', '').strip()

        if not name:
            messages.error(request, 'Vui lòng nhập tên bữa ăn.')
            return render(request, 'meals/create_meal.html', {'group': group, 'members': members, 'today': date.today()})

        # Collect participants + amounts
        participants_data = []
        for m in members:
            uid = str(m.user_id)
            if request.POST.get(f'selected_{uid}'):
                raw = request.POST.get(f'amount_{uid}', '0').replace(',', '').strip()
                try:
                    amt = Decimal(raw)
                except Exception:
                    amt = Decimal('0')
                if amt > 0:
                    participants_data.append((m.user, amt))

        if not participants_data:
            messages.error(request, 'Vui lòng chọn ít nhất một người và nhập số tiền.')
            return render(request, 'meals/create_meal.html', {'group': group, 'members': members, 'today': date.today()})

        with transaction.atomic():
            meal = MealExpense.objects.create(
                group=group,
                name=name,
                date=meal_date,
                note=note,
                created_by=request.user,
            )
            for user, amt in participants_data:
                MealParticipant.objects.create(meal=meal, user=user, amount=amt)
                deduct_for_meal(user, group, amt, meal, request.user)

        total = sum(amt for _, amt in participants_data)
        messages.success(request, f'Đã tạo phiếu "{name}" — tổng {total:,.0f}đ cho {len(participants_data)} người.')
        return redirect('meal_detail', pk=meal.pk)

    return render(request, 'meals/create_meal.html', {
        'group': group,
        'members': members,
        'today': date.today(),
    })


@login_required
def meal_detail(request, pk):
    meal = get_object_or_404(MealExpense, pk=pk)
    group = meal.group
    get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = group.owner == request.user
    participants = list(meal.participants.select_related('user').order_by('-amount'))
    return render(request, 'meals/meal_detail.html', {
        'meal': meal,
        'group': group,
        'participants': participants,
        'is_host': is_host,
    })


@login_required
def meal_list(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    get_object_or_404(GroupMember, group=group, user=request.user, is_active=True)
    is_host = group.owner == request.user
    meals = MealExpense.objects.filter(group=group).prefetch_related('participants')
    # Annotate total for each meal
    for m in meals:
        m.cached_total = sum(p.amount for p in m.participants.all())
        m.cached_count = m.participants.count()
    return render(request, 'meals/meal_list.html', {
        'group': group,
        'meals': meals,
        'is_host': is_host,
    })


@login_required
def delete_meal(request, pk):
    meal = get_object_or_404(MealExpense, pk=pk)
    group = meal.group
    if group.owner != request.user:
        messages.error(request, 'Chỉ chủ nhóm mới có thể xóa phiếu tiền cơm.')
        return redirect('meal_detail', pk=pk)

    if request.method == 'POST':
        meal_name = meal.name
        group_pk = group.pk
        with transaction.atomic():
            for p in meal.participants.select_related('user'):
                refund_for_meal(p.user, group, p.amount, meal_name, request.user)
            meal.delete()
        messages.success(request, f'Đã xóa phiếu "{meal_name}" và hoàn tiền cho tất cả thành viên.')
        return redirect('meal_list', group_pk=group_pk)

    return redirect('meal_detail', pk=pk)
