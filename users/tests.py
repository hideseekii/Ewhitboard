from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_credentials = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'ComplexPwd!123',
            'password2': 'ComplexPwd!123'
        }
        # Register a user for profile tests
        self.user = User.objects.create_user(
            username='existing',
            email='exist@example.com',
            password='TestPwd123'
        )
        # Ensure profile exists if using OneToOne
        if hasattr(self.user, 'profile'):
            self.user.profile.is_registered = False
            self.user.profile.save()

    def test_home_view(self):
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/home.html')

    def test_register_view_get(self):
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_view_post_valid(self):
        response = self.client.post(reverse('users:register'), self.user_credentials)
        # Should redirect to login after successful registration
        self.assertRedirects(response, reverse('users:login'))
        # User should exist
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)

    def test_profile_view_get_login_required(self):
        # Unauthenticated should redirect to login
        response = self.client.get(reverse('users:profile'))
        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('users:profile')}" )

    def test_profile_view_get(self):
        self.client.login(username='existing', password='TestPwd123')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_post(self):
        self.client.login(username='existing', password='TestPwd123')
        # Prepare update data
        new_username = 'updated'
        avatar = SimpleUploadedFile('avatar.png', b'filecontent', content_type='image/png')
        data = {
            'username': new_username,
            'email': 'new@example.com',
            'profile-avatar': avatar
        }
        # The forms expect specific field names; adjust if necessary
        response = self.client.post(reverse('users:profile'), {
            'username': new_username,
            'email': 'new@example.com',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.username, new_username)

    def test_complete_registration_get(self):
        self.client.login(username='existing', password='TestPwd123')
        response = self.client.get(reverse('users:complete_registration'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/complete_registration.html')

    def test_complete_registration_post(self):
        self.client.login(username='existing', password='TestPwd123')
        response = self.client.post(reverse('users:complete_registration'), follow=True)
        self.assertRedirects(response, reverse('users:profile'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.is_registered)

    def test_custom_logout_get(self):
        response = self.client.get(reverse('users:logout'))
        # GET should redirect to home
        self.assertRedirects(response, reverse('users:home'))

    def test_custom_logout_post(self):
        self.client.login(username='existing', password='TestPwd123')
        response = self.client.post(reverse('users:logout'), follow=True)
        self.assertRedirects(response, reverse('users:home'))
        # After logout, user should be anonymous
        response = self.client.get(reverse('users:profile'))
        self.assertRedirects(response, f"{reverse('users:login')}?next={reverse('users:profile')}" )
