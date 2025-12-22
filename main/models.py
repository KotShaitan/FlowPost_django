from django.db import models
from django.contrib.auth.models import User, AbstractUser

class CustomUser(AbstractUser):
    isAuthor = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)

class Post(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    is_premial = models.BooleanField(default=False)
    header = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    images = models.URLField()

class Subscribe_plan(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    describe = models.TextField()
    name = models.TextField()
    price = models.DecimalField(max_digits=7, decimal_places=2)

class Subscribe(models.Model):
    id = models.AutoField(primary_key=True, auto_created=True)
    plan = models.ForeignKey(Subscribe_plan, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_end = models.DateTimeField()
    date_begin = models.DateTimeField()

class PostSubscription(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(Subscribe_plan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)



