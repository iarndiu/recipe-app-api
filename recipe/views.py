from django.shortcuts import render
from .serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer, IngredientSerializer, RecipeImageSerializer
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma seperated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma seperated list of ingredient IDs to filter',
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    '''view for manage recipe APIs'''
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()  # query set that is managable through this API
    authentication_classes = [TokenAuthentication]  # use TokenAuthentication
    permission_classes = [IsAuthenticated]  # user should be authenticated

    def _params_to_ints(self, qs):
        '''convert a list of strings to integers'''
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        '''retrieve recipes for authenticated user'''
        # return self.queryset.filter(user=self.request.user).order_by('-id')
        tags = self.request.query_params.get('tags')
        print(tags)
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            print(tag_ids)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        '''return the serializer class for request'''
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        '''create a new recipe'''
        serializer.save(user=self.request.user)

    @action(methods='POST', detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        '''upload an image to recipe'''
        # get obj using pk
        recipe = self.get_object()
        # if passing an existing instance - update, otherwise - create
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.errors, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes',
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    '''base viewset for recipe attributes'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''filter queryset to authenticated user'''
        assigned_only = bool(int(self.request.query_params.get('assigned_only', 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by('name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    '''manage tags in the databse'''
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    '''manage ingredients in the databse'''
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
