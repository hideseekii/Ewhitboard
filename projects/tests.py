from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Project, ProjectCollaborator

User = get_user_model()

class ProjectViewsTest(TestCase):
    def setUp(self):
        # Users setup
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.collab_user = User.objects.create_user(username='collab', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        # Project and collaborator
        self.project = Project.objects.create(name='TestProj', description='desc', owner=self.owner)
        ProjectCollaborator.objects.create(project=self.project, user=self.collab_user, role='viewer')
        # Client
        self.client = Client()

    def test_project_list_requires_login(self):
        url = reverse('projects:list')
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={url}")

    def test_project_list_shows_owned_and_collaborated(self):
        self.client.login(username='owner', password='pass')
        response = self.client.get(reverse('projects:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.project, response.context['owned_projects'])
        # collab_user sees in collaborated_projects
        self.client.logout()
        self.client.login(username='collab', password='pass')
        response = self.client.get(reverse('projects:list'))
        self.assertIn(self.project, response.context['collaborated_projects'])

    def test_project_create_get_and_post(self):
        url = reverse('projects:create')
        # login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # GET form
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # valid POST
        data = {'name': 'NewProj', 'description': 'new'}
        response = self.client.post(url, data)
        new = Project.objects.filter(name='NewProj', owner=self.owner)
        self.assertTrue(new.exists())
        new_proj = new.first()
        self.assertRedirects(response, reverse('projects:detail', args=[new_proj.pk]))

    def test_project_detail_permission(self):
        url = reverse('projects:detail', args=[self.project.pk])
        # other user -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # collab user -> allowed
        self.client.login(username='collab', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # owner -> allowed
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('collaborators', response.context)
        self.assertIn('boards', response.context)

    def test_project_edit_and_permission(self):
        url = reverse('projects:edit', args=[self.project.pk])
        # other -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # owner GET form
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # owner POST update
        response = self.client.post(url, {'name': 'Updated', 'description': 'desc'})
        self.assertRedirects(response, reverse('projects:detail', args=[self.project.pk]))
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated')

    def test_project_delete_and_permission(self):
        url = reverse('projects:delete', args=[self.project.pk])
        # other -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        # owner GET confirm
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # owner POST delete
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('projects:list'))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_add_and_remove_collaborator(self):
        add_url = reverse('projects:add_collaborator', args=[self.project.pk])
        remove_url = lambda uid: reverse('projects:remove_collaborator', args=[self.project.pk, uid])
        self.client.login(username='owner', password='pass')
        # add new collaborator
        new_user = User.objects.create_user(username='newbie', password='pass')
        response = self.client.post(add_url, {'username': 'newbie', 'role': 'editor'})
        self.assertTrue(self.project.collaborators.filter(username='newbie').exists())
        # update role
        response = self.client.post(add_url, {'username': 'newbie', 'role': 'viewer'})
        collab = ProjectCollaborator.objects.get(project=self.project, user=new_user)
        self.assertEqual(collab.role, 'viewer')
        # remove collaborator
        response = self.client.get(remove_url(new_user.id))
        self.assertFalse(self.project.collaborators.filter(id=new_user.id).exists())

    def test_add_collaborator_permission(self):
        url = reverse('projects:add_collaborator', args=[self.project.pk])
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_remove_collaborator_permission(self):
        url = reverse('projects:remove_collaborator', args=[self.project.pk, self.collab_user.id])
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
