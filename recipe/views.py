from django.shortcuts import render
from .serializers import RecipeSerializer, RecipeDetailSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe


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
