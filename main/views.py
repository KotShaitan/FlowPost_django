from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Post, Subscribe, Subscribe_plan, PostSubscription
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from decimal import Decimal
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from django.db.models import Q


def home_view(request):
    category = request.GET.get('category', 'all')
    
    if request.user.is_authenticated:
        subscribed_authors_ids = Subscribe.objects.filter(
            subscriber=request.user,
            date_end__gt=timezone.now()
        ).values_list('plan__author__id', flat=True).distinct()

        subscribed_plan_ids = Subscribe.objects.filter(
            subscriber=request.user,
            date_end__gt=timezone.now()
        ).values_list('plan__id', flat=True).distinct()
        
        posts = Post.objects.filter(
            Q(is_premial=False) |
            Q(is_premial=True, author__id__in=subscribed_authors_ids) |
            Q(author=request.user)
        ).distinct()

    else:
        posts = Post.objects.filter(is_premial=False)

    # Применяем фильтр по категории ДО пагинации
    if category == 'premium':
        posts = posts.filter(is_premial=True)
    elif category == 'free':
        posts = posts.filter(is_premial=False)
    # category == 'all' - не фильтруем

    # Добавляем сортировку по дате (если есть поле created_at)
    # Если нет поля created_at, можно сортировать по id
    posts = posts.order_by('-id')  # или '-created_at' если есть

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.user.is_authenticated:
        Subscribe.objects.filter(
            subscriber=request.user,
            date_end__gt=timezone.now()
        ).select_related('plan', 'plan__author')
        
    authors = CustomUser.objects.filter(isAuthor=True)[:10]
    
    context = {
        'posts': page_obj,
        'authors': authors,
        'page_obj': page_obj,
        'current_category': category,  # добавляем для шаблона
    }
    return render(request, 'main/home.html', context)
def register_view(request):
    """Отображение окна регистрации"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматически входим после регистрации
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    """Отображение окна авторизации"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'main/login.html', {'form': form})

def logout_view(request):
    """View для выхода из аккаунта"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home') 

@login_required
def create_subscribe_plan(request):
    """View для создания тарифа подписок"""
    if not request.user.isAuthor:

        messages.error(request, "Только авторы могут создавать планы подписки")
        return redirect('home')

    if request.method == 'POST':
        author = request.user
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '')
        describe = request.POST.get('describe', '').strip()
        errors = []
        if not name:
            errors.append("Введите название подписки")
        if not price:
            errors.append("Введите цену")
        price = Decimal(price)
        if price <= 0:
            errors.append("Цена должна быть больше 0")
        if not errors:
            Subscribe_plan.objects.create (
                author=author,
                name=name,
                price=price,
                describe=describe,
            )
        else:
            context = {'errors': errors}
            return render(request, 'main/create_subscribe.html', context)
    return render(request, 'main/create_subscribe.html')

@login_required
def create_post(request):
    """View для создния поста"""
    if not request.user.isAuthor:
        messages.error(request, "Только авторы могут создавать посты")
        return redirect('home')  
    
    subscription_plans = Subscribe_plan.objects.filter(author=request.user)

    if request.method == 'POST':
        header = request.POST.get('header')
        text = request.POST.get('text')
        images = request.POST.get('images')
        is_premial = 'is_premial' in request.POST
        subscription_plan_id = request.POST.get('subscription_plan')
        
        post = Post.objects.create(
            header=header,
            text=text,
            images=images,
            is_premial=is_premial,
            author=request.user
        )
        
        if is_premial and subscription_plan_id:
            try:
                subscription_plan = Subscribe_plan.objects.get(id=subscription_plan_id, author=request.user)
                PostSubscription.objects.create(post=post, subscription_plan=subscription_plan)
                messages.success(request, f'Пост привязан к плану "{subscription_plan.name}"')
            except Subscribe.DoesNotExist:
                messages.warning(request, 'Выбранный план подписки не найден')
        
        return redirect('home')
    
    context = {
        'subscription_plans': subscription_plans
    }
    return render(request, 'main/create_post.html', context)

@login_required
def my_subscriptions(request):
    """View для отображения подписок """
    subscriptions = Subscribe.objects.filter(author=request.user)
    return render(request, 'main/home.html', subscriptions)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from .models import CustomUser, Post, Subscribe_plan, Subscribe, PostSubscription
import datetime

@login_required
def profile(request, id=None):
    """Просмотр профиля пользователя"""
    if request.user is None:
        return redirect('login')
    if id:
        profile_user = get_object_or_404(CustomUser, id=id)
    else:
        profile_user = request.user

    posts = Post.objects.filter(author=profile_user)
    subscription_plans = Subscribe_plan.objects.filter(author=profile_user)
    is_subscribed = False
    active_subscriptions = None
    if profile_user != request.user and profile_user.isAuthor:
        active_subscriptions = Subscribe.objects.filter(
            plan__author=profile_user,
            subscriber=request.user,
            date_end__gt=timezone.now()
        )

        is_subscribed = active_subscriptions.exists()
    
    user_subscriptions = Subscribe.objects.filter(
        subscriber=request.user,
        date_end__gt=timezone.now()
    ).select_related('plan', 'plan__author')
  
    subscribers_count = 0

    if profile_user.isAuthor:
        subscribers_count = Subscribe.objects.filter(
            plan__author=profile_user,
            date_end__gt=timezone.now()
        ).count()

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'subscription_plans': subscription_plans,
        'active_subscriptions': active_subscriptions,
        'user_subscriptions': user_subscriptions,
        'is_subscribed': is_subscribed, 
        'subscribers_count': subscribers_count,
        'is_own_profile': profile_user == request.user,
    }
    
    return render(request, 'main/profile.html', context)

@login_required
def edit_profile_view(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        user = request.user
        user.bio = request.POST.get('bio')       
        user.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')
    
    return render(request, 'main/edit_profile.html')

@login_required
def become_author_view(request):
    """Запрос на получение прав автора"""
    if request.method == 'POST':
    
        request.user.isAuthor = True
        request.user.save()
        
        messages.success(request, 'Вы успешно стали автором! Теперь вы можете создавать посты и планы подписок.')
        return redirect('profile')
    
    return render(request, 'main/become_author.html')

@login_required
def edit_plan_view(request, plan_id):
    """Редактирование плана подписки"""
    plan = get_object_or_404(Subscribe_plan, id=plan_id, author=request.user)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name', plan.name)
        plan.price = request.POST.get('price', plan.price)
        plan.describe = request.POST.get('describe', plan.describe)
        
        plan.save()
        messages.success(request, 'План подписки успешно обновлен!')
        return redirect('profile', id=request.user.id)
    
    context = {
        'plan': plan,
    }
    return render(request, 'main/edit_plan.html', context)

@login_required
def delete_plan_view(request, plan_id):
    """Удаление плана подписки"""
    plan = get_object_or_404(Subscribe_plan, id=plan_id, author=request.user)
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'План подписки успешно удален!')
    
    return redirect('profile', id=request.user.id)

@login_required
def subscribe_to_author_view(request, author_id):
    """Страница оформления подписки на автора"""
    author = get_object_or_404(CustomUser, id=author_id, isAuthor=True)
    
    user_is_subscribed = Subscribe.objects.filter(
        subscriber=request.user,
        plan__author=author,
        date_end__gt=timezone.now()
    ).exists()
    
    active_subscription = None
    if user_is_subscribed:
        active_subscription = Subscribe.objects.filter(
            subscriber=request.user,
            plan__author=author,
            date_end__gt=timezone.now()
        ).first()
    
    plans = Subscribe_plan.objects.filter(author=author)
    
    context = {
        'author': author,
        'plans': plans,
        'user_is_subscribed': user_is_subscribed,
        'active_subscription': active_subscription,
        'posts_count': author.post_set.count(),
        'subscribers_count': Subscribe.objects.filter(plan__author=author).count(),
    }
    
    return render(request, 'main/subscribe.html', context)

@login_required
def process_subscription_view(request, plan_id):
    """Обработка оформления подписки"""
    plan = get_object_or_404(Subscribe_plan, id=plan_id)
    
    existing_subscription = Subscribe.objects.filter(
        subscriber=request.user,
        plan=plan,
        date_end__gt=timezone.now()
    ).exists()
    
    if existing_subscription:
        messages.info(request, 'Вы уже подписаны на этот план!')
        return redirect('profile', id=plan.author.id)
    
    Subscribe.objects.create(
        plan=plan,
        subscriber=request.user,
        date_begin=timezone.now(),
        date_end=timezone.now() + timezone.timedelta(days=30) 
    )
    
    messages.success(request, f'Вы успешно подписались на план "{plan.name}"!')
    return redirect('profile', id=plan.author.id)

@login_required
def unsubscribe_view(request, author_id):
    """Страница отписки от автора"""
    author = get_object_or_404(CustomUser, id=author_id, isAuthor=True)

    subscription = Subscribe.objects.filter(
        subscriber=request.user,
        plan__author=author,
        date_end__gt=timezone.now()
    ).first()
    
    if not subscription:
        messages.info(request, 'У вас нет активной подписки на этого автора')
        return redirect('profile', id=author_id)
    
    if request.method == 'POST':

        subscription.date_end = timezone.now()
        subscription.save()
        
        messages.success(request, f'Вы отписались от {author.username}')
        return redirect('profile', id=author_id)
    
    context = {
        'author': author,
        'subscription': subscription,
    }
    return render(request, 'main/unsubscribe.html', context)