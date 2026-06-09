from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not username or not password:
            messages.error(request, 'Tên đăng nhập và mật khẩu không được để trống')
        elif password != password2:
            messages.error(request, 'Mật khẩu xác nhận không khớp')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Tên đăng nhập "{username}" đã được sử dụng')
        else:
            user = User.objects.create_user(
                username=username, password=password,
                full_name=full_name, email=email, phone=phone,
            )
            login(request, user)
            messages.success(request, f'Chào mừng {user.get_display_name()} đến với ShuttleSplit!')
            return redirect('dashboard')
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        if request.FILES.get('avatar'):
            user.avatar = request.FILES['avatar']
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            user.set_password(new_password)
        user.save()
        if new_password:
            login(request, user)
        messages.success(request, 'Cập nhật thông tin thành công!')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'user': user})
