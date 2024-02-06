'''
tests for user API
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    '''create and return a new user'''
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    '''test the public features of the user API'''

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        '''test creating a user is successful'''
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        '''test error returned if user with email exists'''
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        '''test error returned if password less than 5 chars'''
        payload = {
            'email': 'test@example.com',
            'password': 'te',
            'name': 'test'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''test generates token for valid credentials'''
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        '''test returns error if credentials invalid'''
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test',
        }
        create_user(**user_details)
        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        '''test posting a blank password returns an error'''
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        '''test authentication is required for users'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    '''test API requests that require authentication'''

    def setUp(self):
        self.user = create_user(email='test@example.com',
                                password='testpass123',
                                name='test')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        '''test retrieving profile for logged in user'''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'name': self.user.name, 'email': self.user.email})

    def test_update_user_profile(self):
        '''test updating the user profile for the authenticated user'''
        payload = {'password': 'updatepass', 'name': 'update', }
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
