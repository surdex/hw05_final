from django.forms import ModelForm

from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group']
        error_messages = {
            'text': {
                'required': 'Посты без текста мало кому интересны, '
                            'пожалуйста, поделитесь своей историей!',
            },
        }
