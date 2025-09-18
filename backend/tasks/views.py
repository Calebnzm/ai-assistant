from rest_framework import generics, permissions
from .models import Task
from rest_framework.response import Response
from .serializers import TaskSerializer
from django.utils import timezone
from django.db.models import F, Q
from datetime import datetime, time

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()

        selected_datetime_start = timezone.make_aware(datetime.combine(selected_date, time.min))
        selected_datetime_end = timezone.make_aware(datetime.combine(selected_date, time.max))

        return Task.objects.filter(
            Q(user=self.request.user) & (
                (Q(completion_date__range=(selected_datetime_start, selected_datetime_end)) & Q(due_date__lt=F('completion_date'))) |
                
                (Q(type__in=['habit', 'project']) & Q(due_date__gt=selected_date)) |
                
                (Q(is_completed=False) & Q(due_date__gte=selected_date)) |
                
                Q(completion_date__range=(selected_datetime_start, selected_datetime_end))
            )
        ).order_by("due_date")

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        tasks = self.request.user.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(is_completed=True).count()
        missed_tasks = tasks.filter(is_completed=False, due_date__lt=timezone.now().date()).count()
        active_streaks = tasks.filter(type__in=["habit", "project"], streak__gt=0).count()
        productivity = int((completed_tasks / total_tasks) * 100) if total_tasks else 0

        summary = {
            "user_name": f"{self.request.user.first_name} {self.request.user.last_name}",
            "productivity": productivity,
            "active_streaks": active_streaks,
            "missed_tasks": missed_tasks,
            "date": timezone.now().date()
        }

        return Response({
            "tasks": serializer.data,
            "summary": summary
        })

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        task = serializer.save()
        if task.is_completed:
            if not task.completion_date:
                task.completion_date = timezone.now().date()
                task.save(update_fields=["completion_date"])
        else:
            if task.completion_date:
                task.completion_date = None
                task.save(update_fields=["completion_date"])

        if task.type in ['habit', 'project'] and task.is_completed:
            task.update_streak()