from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.urls import reverse
from django.views.generic import ListView
from .forms import PostForm, UserRegistrationForm, ResponseFilterForm
from .models import Category, Post, Response, Subscription
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from allauth.account.views import SignupView
from django.core.paginator import Paginator


def all_posts(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 5)

    page_number = request.GET.get('page')
    page_posts = paginator.get_page(page_number)

    context = {
        'posts': page_posts,
    }

    return render(request, 'post_list.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    category = post.category
    return render(request, 'post_detail.html', {'post': post, 'category': category})


def send_newsletter(category, post):
    subscriptions = Subscription.objects.filter(category=category)

    for subscription in subscriptions:
        user = subscription.user
        subject = f"Новое объявление в категории {category.name}"
        # Загрузка HTML-шаблона и заполнение контекста
        html_content = render_to_string('newsletter_email.html', {'user': user, 'post': post})

        # Создание объекта EmailMultiAlternatives и добавление альтернативного HTML-контента
        msg = EmailMultiAlternatives(subject, '', 'noreply@yourdomain.com', [user.email])
        msg.attach_alternative(html_content, "text/html")

        # Отправка письма
        msg.send()


@login_required
def subscribe(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    Subscription.objects.get_or_create(user=request.user, category=category)
    messages.success(request, f"Вы успешно подписались на категорию {category.name}.")

    return redirect('post_list')


@login_required
def unsubscribe(request, category_id):
    try:
        subscription = Subscription.objects.get(user=request.user, category_id=category_id)
        subscription.delete()
        messages.success(request, 'Вы успешно отписались от рассылки данной категории.')
    except Subscription.DoesNotExist:
        messages.error(request, 'Вы не подписаны на эту категорию.')

    return redirect('post_list')


class CustomSignupView(SignupView):
    template_name = 'registration/account_confirm_email.html'
    form_class = UserRegistrationForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Пользователь не будет активирован до подтверждения
        user.save()

        confirmation_key = default_token_generator.make_token(user)

        # Отправка письма с ключом подтверждения
        current_site = get_current_site(self.request)
        mail_subject = 'Подтверждение регистрации'
        message = render_to_string(
            'registration/confirmation_email.html',
            {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': confirmation_key,
            }
        )
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.send()

        return redirect('account_confirm_email')


class ConfirmEmailView(SignupView):
    template_name = 'registration/confirm_email.html'

    def dispatch(self, request, *args, **kwargs):
        key = kwargs.get('key')
        try:
            uid = str(urlsafe_base64_decode(key), 'utf-8')
            user = get_user_model().objetcs.get(pk=uid)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, key):
            user.is_active = True
            user.is_verified = True
            user.save()
            return redirect('login')
        else:
            return render(request, 'registration/confirm_email_invalid.html')


class ConfirmEmailInvalidView(SignupView):
    template_name = 'registration/confirm_email_invalid.html'
    name = 'confirm_email_invalid'


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()

            # Вызов функции для отправки уведомлений подписчикам
            send_newsletter(post.category, post)

            return redirect('post_list')
        else:
            print(form.errors)
    else:
        form = PostForm()
    return render(request, 'post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_list')
    else:
        form = PostForm(instance=post)

    return render(request, 'post_edit.html', {'form': form})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('post_list')

    return render(request, 'post_delete.html', {'post': post})


@login_required
def response_create(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.method == 'POST':
        text = request.POST['text']
        Response.objects.create(article=post, sender=request.user, text=text)
        send_mail(
            'Отклик на ваше объявление',
            f'Пользователь {request.user.username} оставил отклик на ваше объявление: {post.title}',
            'noreply@yourdomain.com',
            [post.user.email],
            fail_silently=False,
        )
        messages.success(request, 'Отклик успешно отправлен')
        return redirect('post_list')
    return render(request, 'response_create.html', {'post': post})


@login_required
def response_list(request):
    responses = Response.objects.filter(article__user=request.user)
    return render(request, 'response_list.html', {'responses': responses})


@login_required
def response_list_for_me(request):
    responses_for_me = Response.objects.filter(article__user=request.user)

    form = ResponseFilterForm(request.GET)
    if form.is_valid():
        selected_post = form.cleaned_data['post']
        if selected_post:
            responses_for_me = responses_for_me.filter(article=selected_post)

    return render(request, 'response_list_for_me.html', {'responses_for_me': responses_for_me, 'form': form})


@login_required
def response_accept(request, response_id):
    response = Response.objects.get(id=response_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            send_mail(
                'Ваш отклик принят',
                f'Пользователь {request.user.username} принял ваш отклик на объявление: {response.post.title}',
                'noreply@yourdomain.com',
                [response.sender.email],
                fail_silently=False,
            )
            response.delete()
            messages.success(request, 'Отклик успешно принят')
        elif action == 'reject':
            # Выполните действия по отклонению отклика
            response.delete()
            messages.success(request, 'Отклик отклонен')
        return redirect('response_list')
    return render(request, 'response_accept.html', {'response': response})


@login_required
def response_reject(request, response_id):
    try:
        response = Response.objects.get(id=response_id, article__user=request.user)
        response.delete()
        messages.success(request, 'Отклик успешно отклонен')
    except Response.DoesNotExist:
        messages.error(request, 'Отклик не найден или не принадлежит вам')

    return redirect('response_list_for_me')