from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy

from .models import TFD
from .forms import TFDForm


class TFDListView(ListView):
    model = TFD
    template_name = 'tfd/tfd_list.html'
    context_object_name = 'tfds'


class TFDCreateView(CreateView):
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')


class TFDUpdateView(UpdateView):
    model = TFD
    form_class = TFDForm
    template_name = 'tfd/tfd_form.html'
    success_url = reverse_lazy('tfd-list')


class TFDDetailView(DetailView):
    model = TFD
    template_name = 'tfd/tfd_detail.html'
    context_object_name = 'tfd'
from django.shortcuts import render

# Create your views here.
