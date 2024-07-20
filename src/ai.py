'''the script that handles the interaction with ai'''

import os

from llama_cloud import MessageRole
from llama_index.core import VectorStoreIndex,  Settings
from llama_index.llms.together import TogetherLLM
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core import ChatPromptTemplate
from dotenv import load_dotenv

import session_manager
import aitools

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

print("TOGETHER_API_KEY is " + TOGETHER_API_KEY)

Settings.llm = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", api_key=TOGETHER_API_KEY
)

async def handle_query(current_session: session_manager.Session, user_query: str):
    # TO BE IMPLEMENTED
    await current_session.emit_message(
        session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_LOADING, "Trying to load result right now")
        )
    
    current_session.messages.append(session_manager.Message("User", user_query))

    function_call_msgs = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                """You are a travel ai agent. Your job is to determine which tools/functions are appropriate given a query of 
                travel requirements from a user.\n
                Questions may involve the following topics:\n
                Booking flights\n
                Booking hotels\n

                The Conversation ID is {conversation_id}.\n
                """
            ),
        ),
        ChatMessage(role=MessageRole.USER, content="""
                    User Query:
                    
                    {query}
                    """),
    ]

    message_template = ChatPromptTemplate(function_call_msgs)
    
    print("Conversation ID: " + current_session.conversation_id)
    print("User Query: " + user_query)

    result_formatter_agent = ReActAgent.from_tools([aitools.add_summary_tool, aitools.generate_summary_text_tool], llm=Settings.llm, verbose=True)
    current_session.messages.append(session_manager.Message("AI", ""))
    result_agent_response = result_formatter_agent.chat(message_template.format(query=user_query, conversation_id = current_session.conversation_id))

    #agent = ReActAgent.from_tools([aitools.add_summary_tool], llm=Settings.llm, verbose=True)
    #current_session.messages.append(session_manager.Message("AI", ""))
    #agent_response = agent.chat(message_template.format(history=current_session.get_chat_history(), query=user_query, conversation_id = current_session.conversation_id))
    
    #full_response = ""
    #for message in result_agent_response:
    #    #full_response += message.delta
    #    print(message)

    #current_session.messages.append(session_manager.Message("AI", full_response))

    await on_generation_complete(current_session.conversation_id, current_session.messages[-1].content)
    
    print("Hello World")

async def on_generation_complete(conversation_id: str, response: str):
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    await current_session.emit_message(session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_RESPONSE, response))