import os
from dotenv import load_dotenv
from llama_cloud import ChatMessage, MessageRole
from llama_index.core.tools import FunctionTool
from llama_index.core import ChatPromptTemplate
from llama_index.llms.together import TogetherLLM

import airportsdata

import utilities
import session_manager

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

airports = airportsdata.load('IATA')
llama3 = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", api_key=TOGETHER_API_KEY
)


def get_airport_iana(airport_name: str) -> str:
    '''
    returns the airport IANA code from the airport name
    '''
    for code, airport in airports.items():
        if airport['name'] == airport_name:
            return code
    return None

def generate_summary_text(user_query: str, conversation_id: str) -> str:
    '''
    generates a summary text from the user query
    '''

    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return {"error": "No such conversation exists"}
    
    message_construct = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content= (
            """You are a friendly travel agent. You specialize in booking flights and hotels. Interact in a conversational and casual tone.
               The very first step is to determine what services that user would like to use.
               After determining what services the user wants to use, first write out that information in a list form. 
               Now, your job is to go through the list of services you made and ask questions. Strictly follow the steps presented below.
               
               For booking flights strictly just do the following steps:
               Step 1. Ask about city of departure (city only).
               
               Step 2. Ask about city of arrival (city only).
               
               Step 3. Ask about the departure date (YYYY-MM-DD).
               
               Step 4. Ask about the number of adult travelers (age 12 or older on date of departure).
               
               Step 5. Ask about the travel class (economy, premium economy, business, first).
               
               Step 6. Ask user for confirmation.
               
               Step 7. Go to the next service on your initial list. If there are no more, summarize everything and just output a singular <DONE>.
               
               For booking hotels strictly just do the following steps:
               Step 1. If the user used the booking flights service, infer the city that they would want to stay in. If they did not, then ask the city they would want to stay in.
               
               Step 2. Ask user for confirmation.
               
               Step 3. Go to the next service on your initial list. If there are no more, summarize everything just output a singular <DONE>.
               
               Here is the chat history to help you:
            """
            + current_session.get_chat_history()
                        #   Here is the chat history to help you:
              # {history}
        )
        ),
        ChatMessage(
            role=MessageRole.USER,
            content= user_query,
        ),
    ]
    
    print("user_query: " + user_query)
    print("chat history: " + current_session.get_chat_history())

    #message_template = ChatPromptTemplate(message_construct)

    #print(message_template.format(history=current_session.get_chat_history(), query=user_query))
    llm_response_stream = llama3.stream_complete(str(message_construct))
    full_response = ""
    for message in llm_response_stream:
        full_response += message.delta
    return "The summary text has been generated. You can now add this to the latest message\n \""+full_response+"\""

def add_summary_text(conversation_id: str, text: str):
    '''
    adds a summary text to the latest message that will be displayed to the user
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    if len(current_session.messages) == 0:
        return "There is no messages!"
    
    current_session.messages[-1].content += utilities.SummaryMessage(text).to_json()
    return "Great! Messages has been added. We can end this reAct Agent Session"

def add_possible_places_text(places: list[str]):
    '''
    adds a list of possible places to the latest message that will be displayed to the user
    '''
    return utilities.PossiblePlacesMessage(places).to_json()

def add_possible_flights_text(flights: list[str]):
    '''
    adds a list of possible flights to the latest message that will be displayed to the user
    '''
    return utilities.PossibleFlightsMessage(flights).to_json()

def add_possible_places_to_stay_text(places: list[str]):
    '''
    adds a list of possible places to stay to the latest message that will be displayed to the user
    '''
    return utilities.PossiblePlacesToStayMessage(places).to_json()

def emit_message_generation_completed(conversation_id: str):
    '''
    notifies the server that the message generation using all the other tools has been completed and the frontend can retrieve the latest message
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    current_session.emit_message(session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_RESPONSE, "Server completed loading"))

generate_summary_text_tool = FunctionTool.from_defaults(generate_summary_text)
airport_iana_tool = FunctionTool.from_defaults(get_airport_iana)
add_summary_tool = FunctionTool.from_defaults(add_summary_text)
add_possible_places_tool = FunctionTool.from_defaults(add_possible_places_text)
add_possible_flights_tool = FunctionTool.from_defaults(add_possible_flights_text)
add_possible_places_to_stay_tool = FunctionTool.from_defaults(add_possible_places_to_stay_text)
emit_message_generation_completed_tool = FunctionTool.from_defaults(emit_message_generation_completed)

if __name__ == "__main__":
    print(get_airport_iana("John F Kennedy International Airport"))