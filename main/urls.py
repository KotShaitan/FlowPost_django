from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная страница - используем HomePageView.as_view() для превращения класса в функцию
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:id>', views.profile, name='profile'),
    path('search/', views.search_view, name='search'),
    path('create_post/', views.create_post, name='create_post'),
    path('my_subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('create_subscribe_plan', views.create_subscribe_plan, name="create_subscribe_plan"),
    path('edit_profile/', views.edit_profile_view, name="edit_profile" ),
    path('plan/edit/<int:plan_id>/', views.edit_plan_view, name='edit_plan'),
    path('plan/delete/<int:plan_id>/', views.delete_plan_view, name='delete_plan'),
    path('become_author/', views.become_author_view, name='become_author'),
    path('subscribe/author/<int:author_id>/', views.subscribe_to_author_view, name='subscribe_to_author'),
    path('subscribe/plan/<int:plan_id>/', views.process_subscription_view, name='subscribe_to_plan'),
    path('unsubscribe/<int:author_id>/', views.unsubscribe_view, name='unsubscribe'),

]