from rest_framework import serializers
from .models import User, Achievement, UserAchievement

class UserAchievementStatusSerializer(serializers.ModelSerializer):
    is_achieved = serializers.SerializerMethodField()

    class Meta:
        model = Achievement 
        fields = ['id', 'title', 'description', 'is_achieved']

    def get_is_achieved(self, obj):
        user = self.context.get('user')
        if user is None:
            return False
        return UserAchievement.objects.filter(user=user, achievement=obj).exists()


class ProfileSerializer(serializers.ModelSerializer):
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "bio", "achievements"]
        read_only_fields = ["email"]

    def get_achievements(self, obj):
        all_achievements = Achievement.objects.all()
        serializer = UserAchievementStatusSerializer(
            all_achievements,
            many=True,
            context={"user": obj} 
        )
        return serializer.data


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
