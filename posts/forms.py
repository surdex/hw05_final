from django import forms
from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'image', 'group']
        error_messages = {
            'text': {
                'required': 'Посты без текста мало кому интересны, '
                            'пожалуйста, поделитесь своей историей!',
            },
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widget = {'text': forms.Textarea(attrs={'cols': 80, 'rows': 20})}
