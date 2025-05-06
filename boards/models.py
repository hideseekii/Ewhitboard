from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Board(models.Model):
    """
    單一電子白板，隸屬於某專案。
    """
    title = models.CharField("白板標題", max_length=100)
    project = models.ForeignKey(
        'projects.Project', related_name='boards', on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        User, related_name='created_boards', on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title}（專案：{self.project.name}）"

class BoardCollaborator(models.Model):
    """
    白板層級的成員角色設定（如需更細粒度權限）。
    """
    ROLE_CHOICES = [
        ("viewer", "只讀"),
        ("editor", "可編輯"),
    ]
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField("角色", max_length=10, choices=ROLE_CHOICES, default="editor")
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("board", "user")

    def __str__(self):
        return f"{self.user.username} as {self.role} in {self.board.title}"

class BoardElement(models.Model):
    """
    白板上的繪製元素：筆畫、文字、圖形或嵌入影像。
    使用 JSONField 存放座標、樣式、文字內容等。
    """
    ELEMENT_TYPES = [
        ("stroke", "筆畫"),
        ("text", "文字"),
        ("shape", "圖形"),
        ("image", "影像"),
    ]
    board = models.ForeignKey(Board, related_name='elements', on_delete=models.CASCADE)
    element_type = models.CharField("元素類型", max_length=10, choices=ELEMENT_TYPES)
    data = models.JSONField("繪製資料", help_text="存放座標、顏色、字串等 JSON 結構")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.element_type} on {self.board.title}"  

class BoardSubmission(models.Model):
    """
    記錄送出後的文字辨識結果與時間。
    """
    board = models.ForeignKey(Board, related_name='submissions', on_delete=models.CASCADE)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    recognized_text = models.TextField("辨識結果", blank=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Submission by {self.submitted_by.username} at {self.submitted_at}"

class BoardRecording(models.Model):
    """
    儲存白板的錄影檔案紀錄。
    """
    board = models.ForeignKey(Board, related_name='recordings', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField("錄製檔案", upload_to="board_recordings/")

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"Recording of {self.board.title} at {self.recorded_at}"
