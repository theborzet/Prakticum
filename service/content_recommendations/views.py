from django.shortcuts import render

from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from common.views import TitleMixin

# Create your views here.
class IndexView(TitleMixin, TemplateView):
    template_name = 'content_recommendations\index.html'
    title = 'Welcome'