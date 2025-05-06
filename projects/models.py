# projects/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    """
    專案層級，包含多張白板與協作者設定。
    """
    name = models.CharField("專案名稱", max_length=100)
    description = models.TextField("專案描述", blank=True)
    owner = models.ForeignKey(
        User,
        related_name='owned_projects',
        on_delete=models.CASCADE
    )
    collaborators = models.ManyToManyField(
        User,
        through='ProjectCollaborator',
        related_name='projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}（擁有者：{self.owner.username}）"

class ProjectCollaborator(models.Model):
    """
    定義專案中成員的角色與權限。
    """
    ROLE_CHOICES = [
        ("viewer", "只讀"),
        ("editor", "可編輯"),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField("角色", max_length=10, choices=ROLE_CHOICES, default="viewer")
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")

    def __str__(self):
        return f"{self.user.username} as {self.role} in {self.project.name}"