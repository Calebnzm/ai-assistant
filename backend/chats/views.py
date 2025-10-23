from google import genai
from google.genai import types
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Conversation, ChatMessage
from .serializers import ConversationSerializer
from django.utils import timezone
from datetime import timedelta
from dotenv import load_dotenv
import json
from tools.tool_registry import fetch_schemas, fetch_tools, TOOL_CONFIG
import os

load_dotenv()



class ConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, conversation_id=None):
        user = request.user
        message = request.data.get("message")
        timeout_seconds = 300
            
        conversation = (
            user.conversations.filter(active=True).order_by("-created_at").first()
        )

        if conversation and conversation.is_expired():
            conversation.active = False
            conversation.save()
            conversation = None

        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                expires_at = timezone.now() + timedelta(seconds=timeout_seconds)
            )


        current_time = timezone.now()
        formatted_time = current_time.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        
        system_prompt = f"""
            You are a helpful and efficient AI Personal Assistant for {user.first_name}.
            The current date and time is {formatted_time}. Use this for all date and time context unless the user specifies a different one.

            Primary Capabilities & Tasks:
            You have been provided with tools to explore the user's workspace, and activities. Based on any request the user might have you will be required to:
                1. **Gather all pertinent information:**
                    Before answering or interacting with the user, you will be required at all steps of the conversation to use you tools to gather all the necessary context
                    to best interact and server the user.
                
                2.  **Schedule Jobs and tasks:** 
                    Should the user have any request for any tasks to be taken, you are required to schedule the tasks to be done as the conversation goes on or later. The user 
                    will be briefed upon completion of the task. The woker agents have access to the following tools: {TOOL_CONFIG.get("complete", TOOL_CONFIG)}
            Guidelines for User Interaction:
                To ensure a smooth and efficient experience, please follow these rules:

                    1.  Be Proactive with Questions: If a user's request is ambiguous or missing information needed for a tool (e.g., asking to "schedule a meeting" without a date or time), immediately ask clarifying questions to get all the necessary details at once.
                    2.  Confirm Your Actions: After successfully performing an action (like creating a task or sending an email), clearly summarize what you have done. For example: "Done! I've scheduled 'Team Sync' for 3 PM tomorrow and invited alex@example.com. ✅"
                    3.  Summarize, Then Offer Detail: When retrieving a list of items (like emails or tasks), provide a concise summary first. For example: "I found 3 emails from 'Acme Corp' this week. The subjects are about project updates. Would you like me to read any of them?"
                    4.  Maintain a Friendly Tone: Keep the conversation helpful and approachable. Use emojis where appropriate to make the interaction feel natural and friendly. 😊
                    5.  Prioritize Privacy and Security: Never reveal internal data like user IDs, file IDs, or any code. All your actions should be framed as a personal assistant, not a computer executing functions.
                    6.  When taking any sequence of actions, complete all the actions before resuming to the conversation.
        """

        ChatMessage.objects.create(conversation=conversation, role="user", content=message)

        history = [
            {"role": msg.role, "parts": [{"text": msg.content}]}
            for msg in conversation.messages.all().order_by("created_at")
        ]

        agent = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        tier = "core"
        services = ["in_app", "gmail", "google_docs", "google_drive", "calendar"]
        TOOL_SCHEMAS = fetch_schemas(tier=tier, services=services)
        TOOL_REGISTRY = fetch_tools(tier=tier, services=services)
        tools = types.Tool(function_declarations=TOOL_SCHEMAS)

        response = agent.models.generate_content(
            model="gemini-2.0-flash",
            contents=history,
            config=types.GenerateContentConfig(
                tools=[tools],
                system_instruction=system_prompt
            )
        )

        while True:

            if response.function_calls:
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    tool_args = {key: value for key, value in function_call.args.items()}
                    tool_args["user_id"] = user.id


                    tool_function = TOOL_REGISTRY.get(tool_name)
                    if not tool_function:
                        return Response({"error": f"Tool '{tool_name}' not found."}, status=404)
                    
                    try:
                        tool_result = tool_function(**tool_args)

                    except ValueError as e:
                        tool_result = {
                            "status": "error",
                            "error_type": "VALIDATION_ERROR",
                            "message": "One of the provided arguments has an invalid format.",
                            "details": str(e)
                        }
                        
                    except TypeError as e:
                        tool_result = {
                            "status": "error",
                            "error_type": "ARGUMENT_ERROR",
                            "message": "Missing or incorrect arguments for the tool.",
                            "details": str(e)
                        }
                        
                    except Exception as e:
                        tool_result = {"error": f"An unexpected error occurred: {e}"}
                    if not isinstance(tool_result, dict):
                        tool_result = json.loads(tool_result)
                    print(tool_result)
                    function_response_part = types.Part.from_function_response(
                        name=function_call.name,
                        response=tool_result,
                    )
                    function_response_content = types.Content(
                        role='tool', parts=[function_response_part]
                    )
                    history.append(function_response_content)

                response = agent.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=history,
                    config=types.GenerateContentConfig(
                        tools=[tools],
                        system_instruction=system_prompt
                    )
                )

                continue
            else:
                break

        print(response.text)
        assistant_message = response.text
        ChatMessage.objects.create(conversation=conversation, role="model", content=assistant_message)

        conversation.refresh_expiry(timeout=timeout_seconds)

        return Response({
            "role": "model",
            "content": assistant_message,
            "conversation_id": conversation.id,
            "conversation_expires_at": conversation.expires_at,
        })
    
class ActiveConversationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        timeout_seconds = 60

        conversation = (
            user.conversations.filter(active=True).order_by("-created_at").first()
        )

        if conversation and conversation.is_expired():
            conversation.active = False
            conversation.save()
            conversation = None

        if not conversation:
            conversation = Conversation.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(seconds=timeout_seconds),
            )

        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)

