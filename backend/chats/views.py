
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
from tools.tool_registry import TOOL_REGISTRY, TOOL_SCHEMAS
import requests
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

        system_prompt = f"""
            You are an AI Personal Assistant for {user.first_name}.

            These are your tasks:
                1. Provide the user with any assistance they might require
                2. Schedule activities for the user. They will have to give you all the neccessary info to do that.
                3. Monitor the user's email, calender, and inform them of any impending tasks and activities, as well as schedule them, as they come.
                4. Manage email correspondece for the user.

            When interacting with the client.
                1. Do not provide any code, or confidential information.
                2. Use emoji's as much as you deem neccessary.
                3. Do not lead the conversation except when notifying the user of new activities schedules.    
        """

        ChatMessage.objects.create(conversation=conversation, role="user", content=message)

        history = [
            {"role": msg.role, "parts": [{"text": msg.content}]}
            for msg in conversation.messages.all().order_by("created_at")
        ]

        agent = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        tools = types.Tool(function_declarations=TOOL_SCHEMAS)

        response = agent.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=types.GenerateContentConfig(
                tools=[tools],
                system_instruction=system_prompt
            )
        )

        while True:

            if response.function_calls:
                results = []
                call_logs = []
                for function_call in response.function_calls:
                    tool_name = function_call.name
                    tool_args = {key: value for key, value in function_call.args.items()}
                    tool_args["user_id"] = user.id

                    full_tool_url = f"{request.scheme}://{request.get_host()}/api/chats/agent/execute-tool/"


                    api_response = requests.post(
                        full_tool_url, 
                        json={"tool_name": tool_name, "arguments": tool_args},
                        headers={"Authorization": request.headers.get("Authorization")}
                    )
                    tool_result = api_response.json()
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
                    model="gemini-2.5-flash",
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


# yourapp/views.py

class AgentToolAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tool_name = request.data.get("tool_name")
        arguments = request.data.get("arguments", {})
        
        tool_function = TOOL_REGISTRY.get(tool_name)
        if not tool_function:
            return Response({"error": f"Tool '{tool_name}' not found."}, status=404)
        
        try:
            result = tool_function(**arguments)
            return Response(result)

        # --- MODIFIED ERROR HANDLING BLOCK ---
        except ValueError as e:
            # Catch the specific error from our date parsing
            return Response({
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "One of the provided arguments has an invalid format.",
                "details": str(e) # The message from the exception, e.g., "Invalid date format..."
            }, status=400)
            
        except TypeError as e:
            # This catches missing or incorrect arguments
            return Response({
                "status": "error",
                "error_type": "ARGUMENT_ERROR",
                "message": "Missing or incorrect arguments for the tool.",
                "details": str(e) # e.g., "list_tasks() missing 1 required positional argument: 'end_date_str'"
            }, status=400)
        # --- END OF MODIFICATION ---
            
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {e}"}, status=500)