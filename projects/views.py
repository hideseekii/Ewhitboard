# projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden

from .models import Project, ProjectCollaborator
from .forms import ProjectForm, CollaboratorForm

@login_required
def project_list(request):
    # 用戶擁有的專案
    owned_projects = Project.objects.filter(owner=request.user)
    # 用戶作為協作者的專案
    collaborated_projects = Project.objects.filter(collaborators=request.user).exclude(owner=request.user)
    
    context = {
        'owned_projects': owned_projects,
        'collaborated_projects': collaborated_projects,
    }
    return render(request, 'projects/project_list.html', context)

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f'專案 "{project.name}" 已成功創建！')
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': '創建新專案'})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # 檢查用戶是否有權限查看此專案
    if project.owner != request.user and not project.collaborators.filter(id=request.user.id).exists():
        return HttpResponseForbidden("您沒有權限查看此專案")
    
    # 獲取專案的協作者
    collaborators = ProjectCollaborator.objects.filter(project=project)
    
    # 從 Board 模型獲取白板
    from boards.models import Board
    boards = Board.objects.filter(project=project)
    
    context = {
        'project': project,
        'collaborators': collaborators,
        'boards': boards,
        'is_owner': project.owner == request.user,
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # 只有擁有者可以編輯專案
    if project.owner != request.user:
        return HttpResponseForbidden("只有專案擁有者可以編輯專案")
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'專案 "{project.name}" 已成功更新！')
            return redirect('projects:detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': '編輯專案'})

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # 只有擁有者可以刪除專案
    if project.owner != request.user:
        return HttpResponseForbidden("只有專案擁有者可以刪除專案")
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'專案 "{project_name}" 已成功刪除！')
        return redirect('projects:list')
    
    return render(request, 'projects/project_confirm_delete.html', {'project': project})

@login_required
def add_collaborator(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # 只有擁有者可以添加協作者
    if project.owner != request.user:
        return HttpResponseForbidden("只有專案擁有者可以添加協作者")
    
    if request.method == 'POST':
        form = CollaboratorForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            role = form.cleaned_data['role']
            user = User.objects.get(username=username)
            
            # 確保不會將擁有者添加為協作者
            if user == project.owner:
                messages.error(request, "您不能將自己添加為協作者")
                return redirect('projects:detail', pk=project.pk)
            
            # 檢查用戶是否已經是協作者
            if project.collaborators.filter(id=user.id).exists():
                # 更新角色
                collab = ProjectCollaborator.objects.get(project=project, user=user)
                collab.role = role
                collab.save()
                messages.success(request, f'已更新 {user.username} 的角色為 {collab.get_role_display()}')
            else:
                # 添加新協作者
                ProjectCollaborator.objects.create(project=project, user=user, role=role)
                messages.success(request, f'已將 {user.username} 添加為協作者，角色為 {dict(ProjectCollaborator.ROLE_CHOICES)[role]}')
            
            return redirect('projects:detail', pk=project.pk)
    else:
        form = CollaboratorForm()
    
    return render(request, 'projects/add_collaborator.html', {'form': form, 'project': project})

@login_required
def remove_collaborator(request, pk, user_id):
    project = get_object_or_404(Project, pk=pk)
    
    # 只有擁有者可以移除協作者
    if project.owner != request.user:
        return HttpResponseForbidden("只有專案擁有者可以移除協作者")
    
    user = get_object_or_404(User, pk=user_id)
    
    # 檢查用戶是否是協作者
    if project.collaborators.filter(id=user.id).exists():
        collab = ProjectCollaborator.objects.get(project=project, user=user)
        collab.delete()
        messages.success(request, f'已將 {user.username} 從專案中移除')
    else:
        messages.error(request, f'{user.username} 不是此專案的協作者')
    
    return redirect('projects:detail', pk=project.pk)