from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import json

from projects.models import Project, ProjectCollaborator
from .models import Board, BoardElement, BoardSubmission, BoardRecording

User = get_user_model()

class BoardViewsTest(TestCase):
    def setUp(self):
        # Create users
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.editor = User.objects.create_user(username='editor', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        # Create project and collaborator
        self.project = Project.objects.create(name='Proj', description='desc', owner=self.owner)
        ProjectCollaborator.objects.create(project=self.project, user=self.editor, role='editor')
        # Create a board
        self.board = Board.objects.create(title='Board1', project=self.project, created_by=self.owner)
        self.client = Client()

    def test_board_create_permission(self):
        url = reverse('boards:create', args=[self.project.id])
        # anonymous -> login redirect
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # other user -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # editor -> form
        self.client.login(username='editor', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_board_create_post(self):
        url = reverse('boards:create', args=[self.project.id])
        self.client.login(username='editor', password='pass')
        data = {'title': 'NewBoard'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Board.objects.filter(title='NewBoard', project=self.project).exists())

    def test_board_detail_and_permissions(self):
        url = reverse('boards:detail', args=[self.board.pk])
        # other user -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # editor -> allowed
        self.client.login(username='editor', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('elements', response.context)

    def test_board_edit(self):
        url = reverse('boards:edit', args=[self.board.pk])
        # other -> forbidden
        self.client.login(username='other', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # owner -> form
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # post update
        response = self.client.post(url, {'title': 'Updated'}, follow=True)
        self.assertRedirects(response, reverse('boards:detail', args=[self.board.pk]))
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, 'Updated')

    def test_board_delete(self):
        url = reverse('boards:delete', args=[self.board.pk])
        # editor -> forbidden
        self.client.login(username='editor', password='pass')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        # owner GET -> confirm page
        self.client.login(username='owner', password='pass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # owner POST -> delete and redirect
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('projects:detail', args=[self.project.pk]))
        self.assertFalse(Board.objects.filter(pk=self.board.pk).exists())

    def test_board_elements_crud(self):
        url = reverse('boards:elements', args=[self.board.pk])
        self.client.login(username='owner', password='pass')
        # initial GET -> empty list
        response = self.client.get(url)
        data = response.json()
        self.assertEqual(data['elements'], [])
        # add element
        payload = {'action': 'add', 'element_type': 'text', 'data': 'hello'}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        result = response.json()
        self.assertEqual(result['status'], 'success')
        elem_id = result['element_id']
        # update element
        payload = {'action': 'update', 'element_id': elem_id, 'data': 'world'}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.json()['status'], 'success')
        # delete element
        payload = {'action': 'delete', 'element_id': elem_id}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.json()['status'], 'success')
        # clear
        BoardElement.objects.create(board=self.board, element_type='text', data='x', created_by=self.owner)
        payload = {'action': 'clear'}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.json()['status'], 'success')

    def test_board_export_and_history(self):
        url = reverse('boards:export', args=[self.board.pk])
        self.client.login(username='owner', password='pass')
        # GET should display form and submissions
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # POST export
        data = {'recognized_text': 'test'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BoardSubmission.objects.filter(board=self.board).exists())

    def test_board_record_upload(self):
        url = reverse('boards:record', args=[self.board.pk])
        self.client.login(username='owner', password='pass')
        # GET page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # POST file upload
        dummy = SimpleUploadedFile('rec.mp4', b'data', content_type='video/mp4')
        response = self.client.post(url, {'file': dummy}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(BoardRecording.objects.filter(board=self.board).exists())
