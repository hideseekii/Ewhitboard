# users/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

def home(request):
    """首頁視圖"""
    return render(request, 'users/home.html')

def register(request):
    """用戶註冊視圖"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'帳號 {username} 已創建成功！請登入以完成註冊流程。')
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    """用戶個人資料視圖"""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '您的個人資料已更新！')
            return redirect('users:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'is_registered': request.user.profile.is_registered
    }
    return render(request, 'users/profile.html', context)

@login_required
def complete_registration(request):
    """完成註冊流程，將 is_registered 設置為 True"""
    if request.method == 'POST':
        profile = request.user.profile
        profile.is_registered = True
        profile.save()
        messages.success(request, '註冊完成！您現在可以參與專案了。')
        return redirect('users:profile')
    return render(request, 'users/complete_registration.html')  