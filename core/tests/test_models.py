'''
tests for models
'''
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Recipe, Ingredient, Tag


def create_user(**params):
    '''create and return a new user'''
    return get_user_model().objects.create_user(**params)


class ModelTests(TestCase):
    '''test models'''

    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        name = 'test'
        user = create_user(email=email, name=name, password=password)

        self.assertEqual(user.email, email)
        self.assertEqual(user.name, name)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_nromalized(self):
        '''test email is normalized for new users'''
        sample_emails = [
            ['test1@example.COM', 'test1@example.com'],
            ['teST2@example.COM', 'teST2@example.com'],
            ['test3@exampLE.com', 'test3@example.com'],
        ]

        for email, expected in sample_emails:
            user = create_user(email=email, name='test')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        '''test creating a superuser'''
        with self.assertRaises(ValueError):
            create_user(email='', password='testpass123', name='test')

    def test_create_super_user(self):
        '''test creating a superuser'''
        user = get_user_model().objects.create_superuser(email='admin@example.com',
                                                         password='adminpass123',
                                                         name='admin')

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        '''test creating a recipe is successful'''
        user = create_user(email='test@example.com',
                           password='testpass123',
                           name='test')
        recipe = Recipe.objects.create(
            user=user,
            title='test recipe',
            time_minutes=5,
            description='testesttest',
            price=Decimal('5.5'),
        )

        self.assertEqual(str(recipe), recipe.title)
