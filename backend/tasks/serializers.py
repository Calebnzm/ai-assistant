from rest_framework import serializers
from .models import Task
from datetime import date, timedelta

class TaskSerializer(serializers.ModelSerializer):
    streak_history = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at", "completion_date"]

    def get_streak_history(self, obj):
        selected_date = self.context.get("selected_date", date.today())
        streak_array = []

        streak_dates = [
            d if isinstance(d, date) else date.fromisoformat(d)
            for d in obj.streak_dates or []
        ]

        for i in range (6, -1, -1):
            day = selected_date - timedelta(days=i)

            if day in streak_dates:
                streak_array.append(1)
            else:
                streak_array.append(0)

        return [streak_array, obj.streak or 0]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name}"
    

TASK_TYPE_CHOICES = ["project", "task", "habit"]
PRIORITY_CHOICES = ["high", "medium", "low"]

class ActivityValidatorSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=True)
    description = serializers.CharField(required=True)
    type = serializers.ChoiceField(choices=TASK_TYPE_CHOICES)
    priority = serializers.ChoiceField(choices=PRIORITY_CHOICES)
    
    due_date = serializers.DateField(source="due_date_str", input_formats=["%Y-%m-%d"])
    
    tags = serializers.ListField(child=serializers.CharField(max_length=50))

class ActivityUpdateValidatorSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=TASK_TYPE_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    
    due_date = serializers.DateField(source="due_date_str", input_formats=["%Y-%m-%d"], required=False)

    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)