from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()  # automatically create router
router.register('recipes', views.RecipeViewSet)  # generate url patterns for view
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
