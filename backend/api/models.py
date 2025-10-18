from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    email  = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    telegram_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email


class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

def update_achievements(user):
    """
    Check all possible achievements and grant them to the user if criteria are met.
    """
    # Example achievement rules
    achievements_rules = [
        {"title": "First Task Completed", "criteria": lambda u: u.tasks.filter(is_completed=True).count() >= 1},
        {"title": "Complete 10 Tasks", "criteria": lambda u: u.tasks.filter(is_completed=True).count() >= 10},
        {"title": "First Habit Completed", "criteria": lambda u: u.tasks.filter(is_completed=True, type='habit').count() >= 1},
    ]

    for rule in achievements_rules:
        try:
            achievement = Achievement.objects.get(title=rule["title"])
        except Achievement.DoesNotExist:
            continue

        # Check if user already has it
        already_has = UserAchievement.objects.filter(user=user, achievement=achievement).exists()
        if not already_has and rule["criteria"](user):
            UserAchievement.objects.create(user=user, achievement=achievement)