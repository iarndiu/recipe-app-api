'''
tests for recipe APIs
'''
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Recipe, Ingredient, Tag
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''create and return a recipe detail URL'''
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_user(**params):
    '''create and return a new user'''
    defaults = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'test',
    }
    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def create_recipe(user, **params):
    '''create and return a sample recipe'''
    defaults = {
        'title': 'test recipe',
        'time_minutes': 10,
        'description': 'testesttest',
        'price': Decimal('5.5'),
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    '''test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''test auth is required to call API'''
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    '''test authenticated API requests'''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipe(self):
        '''test retrieve a list of recipes'''
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')  # all recipes
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        '''test list of recipes is limited to authenticated user'''
        new_user = create_user(email='test2@example.com', name='test2')
        create_recipe(user=self.user)
        create_recipe(user=new_user)
        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''test get recipe detail'''
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serizalizer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serizalizer.data)

    def test_create_recipe(self):
        '''test creating a recipe'''
        payload = {
            'title': 'test recipe',
            'time_minutes': 10,
            'description': 'testesttest',
            'price': Decimal('5.5'),
            'link': 'http://example.com/recipe.pdf',
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        '''test partial update a recipe'''
        original_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(user=self.user)
        payload = {'title': 'new title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_recipe(self):
        '''test partial update a recipe'''
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'new recipe',
            'time_minutes': 15,
            'description': 'newtestesttest',
            'price': Decimal('15.5'),
            'link': 'http://example.com/new.pdf',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        '''test changing the recipe user results in an error'''
        recipe = create_recipe(user=self.user)
        new_user = create_user(email='test2@example.com', name='test2')

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        '''test deleting a recipe'''
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        '''test trying to delete another user's recipe gives error'''
        new_user = create_user(email='test2@example.com', name='test2')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        '''test creating a recipe with new tags'''
        payload = {
            'title': 'test recipe',
            'time_minutes': 10,
            'description': 'testesttest',
            'price': Decimal('5.5'),
            'link': 'http://example.com/recipe.pdf',
            'tags': [{'name': 'test1'}, {'name': 'test2'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        '''test creating a recipe with existing tags'''
        tag = Tag.objects.create(user=self.user, name='test')
        payload = {
            'title': 'test recipe',
            'time_minutes': 10,
            'description': 'testesttest',
            'price': Decimal('5.5'),
            'link': 'http://example.com/recipe.pdf',
            'tags': [{'name': 'test'}, {'name': 'test2'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_update_recipe_tags(self):
        '''test creating tag when updating a recipe'''
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [{'name': 'test'}, {'name': 'test2'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag1 = Tag.objects.get(user=self.user, name='test')
        new_tag2 = Tag.objects.get(user=self.user, name='test2')
        self.assertIn(new_tag1, recipe.tags.all())
        self.assertIn(new_tag2, recipe.tags.all())

    def test_update_recipe_assign_tags(self):
        '''test assigning an existing tag when updating a recipe'''
        tag = Tag.objects.create(user=self.user, name='test')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        tag2 = Tag.objects.create(user=self.user, name='test2')
        payload = {
            'tags': [{'name': 'test2'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag, recipe.tags.all())

    def test_clear_recipe_tags(self):
        '''test clearing a recipe tags'''
        tag = Tag.objects.create(user=self.user, name='test')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)
