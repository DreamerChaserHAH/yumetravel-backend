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

llama3 = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", api_key=TOGETHER_API_KEY
)

async def handle_query(current_session: session_manager.Session, user_query: str):
    # TO BE IMPLEMENTED
    #await current_session.emit_message(
    #    session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_LOADING, "Trying to load result right now")
    #    )
    current_session.status = session_manager.SessionStatus.LOADING

    #current_session.messages.append(session_manager.Message("User", user_query))

    #summary_text = aitools.generate_summary_text(user_query, current_session.conversation_id)
    #current_session.messages.append(session_manager.Message("AI", ""))

    summary_text = aitools.generate_summary_text(user_query, current_session.conversation_id)
    print("The summary text is: " + summary_text)
    aitools.add_summary_text(conversation_id=current_session.conversation_id, text=summary_text)

    function_call_msgs = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=(
                """You are a reAct Agent that augments the generated response of a NLP Agent that generates questions or recommendations. Your job is to use tools/functions at your disposal to.\n
                1. Look at the summary text
                2. Use the tools that you find that will augment the summary text

                The Conversation ID is {conversation_id}.\n

                End the session if you find no relevant tools to use.

                DO NOT EXECUTE ANY TOOLS MORE THAN ONCE\n

                CONTEXT: \n{context}
                """
            ),
        ),
        ChatMessage(role=MessageRole.CHATBOT, content="""
                    Summary:
                    
                    """ + summary_text),
    ]

    message_template = ChatPromptTemplate(function_call_msgs)
    
    #print("Conversation ID: " + current_session.conversation_id)
    #print("User Query: " + user_query)

    """llama3.chat_with_tools(
        tools=[
            aitools.add_possible_flights_tool,
            aitools.airport_iana_tool,
            aitools.get_today_tool,
            aitools.end_message_tool
        ],
        user_msg=message_template.format(conversation_id = current_session.conversation_id),
        
        )
        """

    result_formatter_agent = ReActAgent.from_tools([
        aitools.add_possible_flights_tool,
        aitools.add_possible_places_tool,
        #aitools.airport_iata_tool,
        aitools.get_today_tool,
        aitools.end_message_tool,
        aitools.update_context_tool
        ], 
        llm=llama3,
        verbose=True,
        context=current_session.context,
        max_iterations=20
        )
    
    result_agent_response = result_formatter_agent.chat(message_template.format(conversation_id = current_session.conversation_id, context = current_session.context))
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
    current_session.status = session_manager.SessionStatus.COMPLETED
    #await current_session.emit_message(session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_RESPONSE, response))