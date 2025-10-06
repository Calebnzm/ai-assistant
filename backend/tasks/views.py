from rest_framework import generics, permissions
from .models import Task
from rest_framework.response import Response
from .serializers import TaskSerializer
from django.utils import timezone
from django.db.models import F, Q
from datetime import datetime, time
from api.models import update_achievements

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        today = timezone.now().date()
        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()

        if selected_date == today:
            return Task.objects.filter(
                Q(user=self.request.user) & (
                    Q(type__in=['habit', 'project'], created_at__date__lte=selected_date, due_date__gte=selected_date) |
                    
                    Q(type='task', is_completed=False, created_at__date__lte=selected_date) |
                    
                    Q(type='task', completion_date__date=selected_date)
                )
            ).order_by("due_date")
        
        elif selected_date > today:
            return Task.objects.filter(
                Q(user=self.request.user) & (
                    Q(type__in=['habit', 'project'], created_at__date__lte=selected_date, due_date__gte=selected_date) |
                    
                    Q(type='task', is_completed=False, created_at__date__lte=selected_date)
                )
            ).order_by("due_date")
        
        else:
            return Task.objects.filter(
                Q(user=self.request.user) & (
                    Q(type__in=['habit', 'project'], created_at__date__lte=selected_date, due_date__gte=selected_date) |
                    
                    Q(type='task', due_date=selected_date, completion_date__date__gt=F('due_date')) |

                    Q(type='task', is_completed=False, due_date__lte=selected_date) |
                    
                    Q(type='task', completion_date__date=selected_date)
                )
            ).order_by("due_date")

    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = timezone.now().date()
        else:
            selected_date = timezone.now().date()
        
        serializer = self.get_serializer(queryset, many=True, context={"selected_date": selected_date})

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
        today = timezone.localdate()

        if task.is_completed:
            if not task.completion_date:
                task.completion_date = timezone.now()

            if task.type in ['habit', 'project']:
                task.update_streak(today)

        else:
            task.completion_date = None
            if task.type in ['habit', 'project']:
                task.mark_incomplete()

        task.save(update_fields=["completion_date", "streak", "streak_dates", "last_completed"])
        update_achievements(self.request.user)
