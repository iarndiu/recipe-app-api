from django.shortcuts import render
from .serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer, IngredientSerializer
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient


class RecipeViewSet(viewsets.ModelViewSet):
    '''view for manage recipe APIs'''
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()  # query set that is managable through this API
    authentication_classes = [TokenAuthentication]  # use TokenAuthentication
    permission_classes = [IsAuthenticated]  # user should be authenticated

    def get_queryset(self):
        '''retrieve recipes for authenticated user'''
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        '''return the serializer class for request'''
        if self.action == 'list':
            return RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        '''create a new recipe'''
        serializer.save(user=self.request.user)


class BaseRecipeAttrViewSet(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    '''base viewset for recipe attributes'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''filter queryset to authenticated user'''
        return self.queryset.filter(user=self.request.user).order_by('name')


class TagViewSet(BaseRecipeAttrViewSet):
    '''manage tags in the databse'''
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    '''manage ingredients in the databse'''
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
