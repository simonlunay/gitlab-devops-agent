import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import root_agent

APP_NAME = "gitlab_devops_agent"
USER_ID = "user1"
SESSION_ID = "session1"

async def main():
    session_service = InMemorySessionService()
    
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    print("GitLab DevOps Agent ready! Type your message below.")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        
        response = runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        )
        
        for event in response:
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(f"Agent: {event.content.parts[0].text}\n")
asyncio.run(main())