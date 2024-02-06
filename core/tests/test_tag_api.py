'''
tests for tag APIs
'''
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Recipe, Ingredient, Tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer

TAG_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    '''create and return a tag detail URL'''
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(**params):
    '''create and return a new user'''
    defaults = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'test',
    }
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_tag(user, **params):
    '''create and return a sample tag'''
    defaults = {
        'name': 'test tag',
    }
    defaults.update(params)

    tag = Tag.objects.create(user=user, **defaults)
    return tag


class PublicRecipeAPITests(TestCase):
    '''test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''test auth is required to call API'''
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    '''test authenticated API requests'''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tag(self):
        '''test retrieve a list of tags'''
        create_tag(user=self.user)
        create_tag(user=self.user)
        res = self.client.get(TAG_URL)

        tags = Tag.objects.all().order_by('-name')  # all tags
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tag_list_limited_to_user(self):
        '''test list of tags is limited to authenticated user'''
        new_user = create_user(email='test2@example.com', name='test2')
        tag = create_tag(user=self.user)
        create_tag(user=new_user, name='test2')
        res = self.client.get(TAG_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''test update a tag'''
        tag = create_tag(user=self.user)
        payload = {'name': 'new tag'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        '''test deleting a tag'''
        tag = create_tag(user=self.user)
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
