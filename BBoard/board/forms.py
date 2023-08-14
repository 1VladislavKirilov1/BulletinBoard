from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives

from .models import Post


class ResponseFilterForm(forms.Form):
    post = forms.ModelChoiceField(queryset=Post.objects.all(), empty_label="Все объявления", required=False)


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'text', 'category', 'upload']

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        title = cleaned_data.get("title")

        if title == category:
            raise ValidationError(
                "Заголовок не должен совпадать с категорией."
            )

        return cleaned_data

    def save(self, commit=True, user=None):
        post = super().save(commit=False)
        if user:
            post.user = user
        if commit:
            post.save()
        return post


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    confirmation_key = forms.CharField(label="Ключ подтверждения", max_length=6)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            confirmation_key = self.cleaned_data['confirmation_key']
            if user.profile.confirmation_key == confirmation_key:
                user.profile.confirmed = True
                user.profile.save()
            subject = 'Добро пожаловать на нашу доску объявлений!'
            text = f'{user.username}, вы успешно зарегистрировались на сайте!'
            html = (
                f'<b>{user.username}</b>, вы успешно зарегистрировались на '
                f'<a href="http://127.0.0.1:8000/post/list">сайте</a>!'
            )
            msg = EmailMultiAlternatives(
                subject=subject, body=text, from_email='noreply@yourdomain.com', to=[user.email]
            )
            msg.attach_alternative(html, "text/html")
            msg.send()

        return user