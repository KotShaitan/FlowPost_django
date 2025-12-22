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
    # Получаем все посты, отсортированные по дате (добавьте поле created_date в модель Post)
    posts = Post.objects.all()
    
    if request.user.is_authenticated:
        # Получаем авторов, на которых подписан пользователь
        subscribed_authors_ids = Subscribe.objects.filter(
            subscriber=request.user,
            date_end__gt=timezone.now()
        ).values_list('plan__author__id', flat=True).distinct()
        
        posts = Post.objects.filter(
            Q(is_premial=False) |  # Бесплатные посты
            Q(is_premial=True, author__id__in=subscribed_authors_ids) |  # Премиум посты от подписанных авторов
            Q(author=request.user)  # Собственные посты
        ).distinct()

    else:
        posts = Post.objects.filter(is_premial=False)
    # Пагинация
    paginator = Paginator(posts, 10)  # 10 постов на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем подписки пользователя, если он авторизован
    subscriptions = []
    if request.user.is_authenticated:
        subscriptions = Subscribe.objects.filter(
            subscriber=request.user,
            date_end__gt=timezone.now()
        ).select_related('plan', 'plan__author')
        
    # Получаем авторов для подписок в боковой панели
    authors = CustomUser.objects.filter(isAuthor=True)[:10]
    
    context = {
        'posts': page_obj,
        'authors': authors,
        'page_obj': page_obj,
    }
    return render(request, 'main/home.html', context)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматически входим после регистрации
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
        else:
            # Покажем ошибки формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
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
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('home') 

@login_required
def create_subscribe_plan(request):
    if not request.user.isAuthor:
        # Можно добавить сообщение об ошибке или редирект
        messages.error(request, "Только авторы могут создавать планы подписки")
        return redirect('home')  # или другая страница

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
    if not request.user.isAuthor:
        messages.error(request, "Только авторы могут создавать посты")
        return redirect('home')  # или другая страница
    
    subscription_plans = Subscribe_plan.objects.filter(author=request.user)

    if request.method == 'POST':
        header = request.POST.get('header')
        text = request.POST.get('text')
        images = request.POST.get('images')
        is_premial = 'is_premial' in request.POST
        subscription_plan_id = request.POST.get('subscription_plan')
        
        # Создаем пост
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

def search_view(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'relevance')
    results = []
    
    if query:
        results = Post.objects.filter(
            Q(header__icontains=query) |
            Q(text__icontains=query) |
            Q(author__username__icontains=query)
        )
        
        # Применяем сортировку
        if sort == 'new':
            results = results.order_by('-created_date')
        elif sort == 'premium':
            results = results.filter(is_premial=True).order_by('-id')
        elif sort == 'free':
            results = results.filter(is_premial=False).order_by('-id')
        else:
            # Сортировка по релевантности (простая версия)
            results = results.order_by('-id')
    
    # Популярные теги для предложений
    trending_tags = ['Python', 'Django', 'Веб-разработка', 'Дизайн', 'Бизнес', 'Технологии', 'Стартапы']
    
    context = {
        'query': query,
        'results': results,
        'sort': sort,
        'trending_tags': trending_tags,
    }
    return render(request, 'search.html', context)

@login_required
def my_subscriptions(request):
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
    # Если username не указан, показываем свой профиль
    if id:
        profile_user = get_object_or_404(CustomUser, id=id)
    else:
        profile_user = request.user
    
    # Статистика пользователя
    posts = Post.objects.filter(author=profile_user)
    subscription_plans = Subscribe_plan.objects.filter(author=profile_user)
    is_subscribed = False  # <-- Добавляем эту переменную
    
    # Активные подписки пользователя (если смотрим чужой профиль)
    active_subscriptions = None
    if profile_user != request.user and profile_user.isAuthor:
        active_subscriptions = Subscribe.objects.filter(
            plan__author=profile_user,
            subscriber=request.user,
            date_end__gt=timezone.now()
        )

        is_subscribed = active_subscriptions.exists()
    
    # Подписки пользователя на других авторов
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
        # Здесь можно добавить логику отправки заявки администратору
        # или автоматически присвоить права (не рекомендуется)
        
        # Временно: автоматически делаем автором
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
        # Обновляем поля плана
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
    
    # Проверяем, подписан ли уже пользователь
    user_is_subscribed = Subscribe.objects.filter(
        subscriber=request.user,
        plan__author=author,
        date_end__gt=timezone.now()
    ).exists()
    
    # Получаем активную подписку (если есть)
    active_subscription = None
    if user_is_subscribed:
        active_subscription = Subscribe.objects.filter(
            subscriber=request.user,
            plan__author=author,
            date_end__gt=timezone.now()
        ).first()
    
    # Получаем планы подписки автора
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
    
    # Проверяем, не подписан ли уже пользователь
    existing_subscription = Subscribe.objects.filter(
        subscriber=request.user,
        plan=plan,
        date_end__gt=timezone.now()
    ).exists()
    
    if existing_subscription:
        messages.info(request, 'Вы уже подписаны на этот план!')
        return redirect('profile', id=plan.author.id)
    
    # Создаем подписку
    Subscribe.objects.create(
        plan=plan,
        subscriber=request.user,
        date_begin=timezone.now(),
        date_end=timezone.now() + timezone.timedelta(days=30)  # 30 дней
    )
    
    messages.success(request, f'Вы успешно подписались на план "{plan.name}"!')
    return redirect('profile', id=plan.author.id)

@login_required
def unsubscribe_view(request, author_id):
    """Страница отписки от автора"""
    author = get_object_or_404(CustomUser, id=author_id, isAuthor=True)
    
    # Получаем активную подписку пользователя
    subscription = Subscribe.objects.filter(
        subscriber=request.user,
        plan__author=author,
        date_end__gt=timezone.now()
    ).first()
    
    # Если нет активной подписки
    if not subscription:
        messages.info(request, 'У вас нет активной подписки на этого автора')
        return redirect('profile', id=author_id)
    
    # Если POST запрос - отписываем
    if request.method == 'POST':
        # Просто завершаем подписку (устанавливаем дату окончания на текущую)
        subscription.date_end = timezone.now()
        subscription.save()
        
        messages.success(request, f'Вы отписались от {author.username}')
        return redirect('profile', id=author_id)
    
    # Если GET запрос - показываем страницу подтверждения
    context = {
        'author': author,
        'subscription': subscription,
    }
    return render(request, 'main/unsubscribe.html', context)