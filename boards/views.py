from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Board, BoardElement, BoardCollaborator, BoardSubmission, BoardRecording
from .forms import BoardForm, BoardSubmissionForm
from projects.models import Project, ProjectCollaborator

@login_required
def board_create(request, project_id):
    """創建新白板"""
    project = get_object_or_404(Project, id=project_id)
    
    # 檢查用戶是否有權限在該專案創建白板
    if project.owner != request.user and not ProjectCollaborator.objects.filter(
            project=project, user=request.user, role='editor').exists():
        return HttpResponseForbidden("您沒有權限在此專案創建白板")
    
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.project = project
            board.created_by = request.user
            board.save()
            messages.success(request, f'白板 "{board.title}" 已成功創建！')
            return redirect('boards:detail', pk=board.pk)
    else:
        form = BoardForm()
    
    return render(request, 'boards/board_form.html', {
        'form': form, 
        'title': '創建新白板',
        'project': project
    })

@login_required
def board_detail(request, pk):
    """查看白板詳情和繪圖介面"""
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限查看此白板
    if project.owner != request.user and not project.collaborators.filter(id=request.user.id).exists():
        return HttpResponseForbidden("您沒有權限查看此白板")
    
    # 確定用戶的編輯權限
    is_owner = project.owner == request.user
    can_edit = is_owner or ProjectCollaborator.objects.filter(
        project=project, user=request.user, role='editor').exists()
    
    # 獲取白板上的元素
    elements = list(board.elements.all().values())
    
    context = {
        'board': board,
        'project': project,
        'elements': json.dumps(elements),
        'is_owner': is_owner,
        'can_edit': can_edit,
    }
    return render(request, 'boards/board_detail.html', context)

@login_required
def board_edit(request, pk):
    """編輯白板信息"""
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限編輯此白板
    if project.owner != request.user and not ProjectCollaborator.objects.filter(
            project=project, user=request.user, role='editor').exists():
        return HttpResponseForbidden("您沒有權限編輯此白板")
    
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            messages.success(request, f'白板 "{board.title}" 信息已更新！')
            return redirect('boards:detail', pk=board.pk)
    else:
        form = BoardForm(instance=board)
    
    return render(request, 'boards/board_form.html', {
        'form': form, 
        'title': '編輯白板信息',
        'project': project,
        'board': board
    })

@login_required
def board_delete(request, pk):
    """刪除白板"""
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限刪除此白板
    if project.owner != request.user:
        return HttpResponseForbidden("只有專案擁有者可以刪除白板")
    
    if request.method == 'POST':
        project_id = project.id  # 在刪除白板前保存專案ID
        board_title = board.title
        board.delete()
        messages.success(request, f'白板 "{board_title}" 已成功刪除！')
        return redirect('projects:detail', pk=project_id)
    
    return render(request, 'boards/board_confirm_delete.html', {
        'board': board,
        'project': project
    })

@login_required
@csrf_exempt
def board_elements(request, pk):
    """處理白板元素的添加/更新/刪除"""
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限編輯此白板
    if project.owner != request.user and not ProjectCollaborator.objects.filter(
            project=project, user=request.user, role='editor').exists():
        return JsonResponse({'status': 'error', 'message': '您沒有權限編輯此白板'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'add':
            element = BoardElement.objects.create(
                board=board,
                element_type=data.get('element_type'),
                data=data.get('data'),
                created_by=request.user
            )
            return JsonResponse({
                'status': 'success', 
                'element_id': element.id,
                'message': '元素已添加'
            })
            
        elif action == 'update':
            element_id = data.get('element_id')
            try:
                element = BoardElement.objects.get(id=element_id, board=board)
                element.data = data.get('data')
                element.save()
                return JsonResponse({'status': 'success', 'message': '元素已更新'})
            except BoardElement.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '找不到該元素'}, status=404)
                
        elif action == 'delete':
            element_id = data.get('element_id')
            try:
                element = BoardElement.objects.get(id=element_id, board=board)
                element.delete()
                return JsonResponse({'status': 'success', 'message': '元素已刪除'})
            except BoardElement.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '找不到該元素'}, status=404)
                
        elif action == 'clear':
            # 清除白板上的所有元素
            BoardElement.objects.filter(board=board).delete()
            return JsonResponse({'status': 'success', 'message': '白板已清除'})
                
        return JsonResponse({'status': 'error', 'message': '無效的操作'}, status=400)
        
    elif request.method == 'GET':
        # 返回白板上的所有元素
        elements = list(board.elements.all().values())
        return JsonResponse({'elements': elements})
    
    return JsonResponse({'status': 'error', 'message': '不支持的請求方法'}, status=405)

@login_required
def board_export(request, pk):
    """導出白板內容（文字辨識結果）"""
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限訪問此白板
    if project.owner != request.user and not project.collaborators.filter(id=request.user.id).exists():
        return HttpResponseForbidden("您沒有權限訪問此白板")
    
    if request.method == 'POST':
        form = BoardSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.board = board
            submission.submitted_by = request.user
            submission.save()
            messages.success(request, '白板內容已成功匯出！')
            
            # 根據需求返回導出結果或重定向
            if request.POST.get('return_json'):
                return JsonResponse({
                    'status': 'success',
                    'submission_id': submission.id,
                    'recognized_text': submission.recognized_text
                })
            return redirect('boards:detail', pk=board.pk)
    else:
        form = BoardSubmissionForm()
    
    # 獲取白板的歷史提交記錄
    submissions = board.submissions.all()
    
    return render(request, 'boards/board_export.html', {
        'board': board,
        'project': project,
        'form': form,
        'submissions': submissions
    })

@login_required
def board_record(request, pk):
    board = get_object_or_404(Board, pk=pk)
    project = board.project
    
    # 檢查用戶是否有權限訪問此白板
    if project.owner != request.user and not project.collaborators.filter(id=request.user.id).exists():
        return HttpResponseForbidden("您沒有權限訪問此白板")
    
    if request.method == 'POST':
        if 'file' in request.FILES:
            recording = BoardRecording.objects.create(
                board=board,
                recorded_by=request.user,
                file=request.FILES['file']
            )
            messages.success(request, '錄製已保存！')
            
            if request.POST.get('return_json'):
                return JsonResponse({
                    'status': 'success',
                    'recording_id': recording.id,
                    'url': recording.file.url
                })
            return redirect('boards:detail', pk=board.pk)
    
    # 獲取白板的所有錄制記錄
    recordings = board.recordings.all()
    
    return render(request, 'boards/board_record.html', {
        'board': board,
        'project': project,
        'recordings': recordings
    })