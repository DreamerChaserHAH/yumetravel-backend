import json
import os
import requests

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
AMADEUS_API_URL = os.getenv("AMADEUS_API_URL")
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

airports = airportsdata.load('IATA')
llama3 = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", api_key=TOGETHER_API_KEY
)

amadeus_token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
token_request_headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
token_request_data = {
    "grant_type": "client_credentials",
    "client_id": AMADEUS_API_KEY,
    "client_secret": AMADEUS_API_SECRET
}

response = requests.post(amadeus_token_url, headers=token_request_headers, data=token_request_data)
print(response.json())
amadeus_access_token = response.json()["access_token"]

authorization_header = {
    "Authorization": "Bearer " + amadeus_access_token
}

amadeus_flight_offers_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
amadeus_activities_url = "https://test.api.amadeus.com/v1/shopping/activities"

def get_today() -> str:
    '''
    returns the current date in the format YYYY-MM-DD
    '''
    from datetime import date
    today = date.today()
    return today.strftime("%Y-%m-%d")

def get_airport_iata(airport_name: str) -> str:
    '''
    parameter:\n
    airport_name: the full name of the airport\n

    uses this function if you want to make certain of airport code
    returns the airport IATA code from the full airport name

    Ensures that you convert city name to their international airports for this function to work
    '''
    for code, airport in airports.items():
        if airport['name'] == airport_name:
            return code
    return "Your input is not a valid airport name. End the conversation and ask it from the user.     if you already knows which airport the user is most likely heading to, input the full airport name instead"

def generate_summary_text(user_query: str, conversation_id: str) -> str:
    '''
    generates a summary text from the user query
    '''

    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return {"error": "No such conversation exists"}
    
    current_session.messages.append(session_manager.Message("User", user_query))

    #summary_text = aitools.generate_summary_text(user_query, current_session.conversation_id)

    message_construct = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content= (
            """You are a friendly travel agent. You specialize in booking flights and hotels. Interact in a conversational and casual tone.
               The very first step is to determine what services that user would like to use.
               After determining what services the user wants to use, first write out that information in a list form. 
               Now, your job is to go through the list of services you made and ask questions. Strictly follow the steps presented below.
               
               For booking flights strictly just do the following steps:
                Step 1. Ask about city of departure (city only). Skip this step if the user has already mentioned it.
               
               Step 2. Ask about city of arrival (city only). Skip this step if the user has already mentioned it.
               
               Step 3. Ask about the departure date (YYYY-MM-DD). Skip this step if the user has already mentioned it.
               
               Step 4. Ask about the number of adult travelers (age 12 or older on date of departure). Skip this step if the user has already mentioned it.
               
               Step 5. Ask about the travel class (economy, premium economy, business, first). Skip this step if the user has already mentioned it.
               
               Step 6. Ask user for confirmation.
               
               Step 7. Go to the next service on your initial list. If there are no more, summarize everything and just output a singular <DONE>.
               
               For booking hotels strictly just do the following steps:
               Step 1. If the user used the booking flights service, infer the city that they would want to stay in. If they did not, then ask the city they would want to stay in. If they already specified the city you don't have to ask anything.
               
               Step 2. Ask user for confirmation.
               
               Step 3. Go to the next service on your initial list. If there are no more, summarize everything just output a singular <DONE>.
               
               Give the final summary as a list of information for each service the user used.
               Booking flights:
               1.City of departure
               2.City of Arrival
               3.Number of Adult Travelers
               4.Travel Class
               
               Booking hotels:
               1.City of Stay
               
               Here is the chat history to help you:\n

               {history}
            """
            #+ current_session.get_chat_history()
                        #   Here is the chat history to help you:
              # {history}
        ),
        additional_kwargs=[]
        ),
        ChatMessage(
            role=MessageRole.USER,
            content=(
                """
                {query}
                """
            ),
            additional_kwargs=[]
        ),
    ]
    
    message_template = ChatPromptTemplate(message_templates = message_construct)

    current_session.messages.append(session_manager.Message("AI", ""))
    #message_template = ChatPromptTemplate(message_construct)

    #print(message_template.format(history=current_session.get_chat_history(), query=user_query))
    llm_response = llama3.complete(
    message_template.format( history=current_session.get_chat_history(), query=user_query))
    #full_response = ""
    #for message in llm_response_stream:
    #    full_response += message.delta
    return llm_response.text

def add_summary_text(conversation_id: str, text: str):
    '''
    adds a summary text to the latest message that will be displayed to the user
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    if len(current_session.messages) == 0:
        return "There is no messages!"
    
    current_session.messages[-1].content += text
    current_session.messages[-1].responses.append(utilities.SummaryMessage(text).construct())

def add_possible_places_text(conversation_id: str, latitude: float, longitude: float):
    '''
    adds a list of possible activities to do around a particular coordinate

    if you don't have the latitude and longitude, possibly convert the city name to the latitude and longitude

    this function adds the list of possible places that the user can visit at a particular destination to the latest message that will be displayed to the user

    Use this function when the user is looking for places to visit at a particular destination, or you think the function is relevant to the summary
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return "The conversation is invalid! It is impossible to do anything. Quit the conversation"
    
    search_place_request_params = {
        "latitude": latitude,
        "longitude": longitude
    }
    activities_response = requests.get(amadeus_activities_url, headers=authorization_header, params = search_place_request_params)
    places = []
    print(activities_response.json()["data"])
    for activity in activities_response.json()["data"]:
        places.append({
            "Name": activity["name"],
            "Description": activity["description"],
            #"Rating": activity["rating"],
            "Price": activity["price"],
            #"Rating": activity["rating"],
            "Pictures": activity["pictures"],
            #"Booking Link": activity["bookingLink"]
        })
    print(places)

    current_session.messages[-1].responses.append(utilities.PossiblePlacesMessage(places).construct())
    # 1. Search for Places to Visit
    return "Great! Possible activities to do in a particular place have been added to the latest message."

def add_possible_flights_text(conversation_id: str, originLocationCode: str, destinationLocationCode: str, departureDate: str, adults: int = 1):
    '''
    Use this tool only when the current summary is relevant to flights
    make sure you convert city names to their relevant international airport IATA code for this function to work\n
    adds a list of possible flights to the latest message that will be displayed to the user\n
    Use other tools to figure out what tools are necessary to get some of those values if they are missing\n
    parameter summary:\n
    originLocationCode: the IANA code of the origin location\n
    destinationLocationCode: the IANA code of the destination location\n
    departureDate: the date of departure in the format YYYY-MM-DD\n
    adults: the number of adults
    '''

    # 1. Search for Available Flights to a particular place and their pricing
    # 2. Get the possible flights from one place to another including multiple information
    # - Time it takes
    # - Airline
    # - Price

    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return "The conversation is invalid! It is impossible to do anything. Quit the conversation"

    if len(originLocationCode) == 0 or len(destinationLocationCode) == 0 or len(departureDate) == 0 or adults == -1 :
        return "There isn't enough detail to use this tool yet. Try using other tools like get_today and revisit this tool"

    flight_offers_request_data = {
        "originLocationCode": originLocationCode,
        "destinationLocationCode": destinationLocationCode,
        "departureDate": departureDate,
        "adults": adults,
        "max": 3,
        "currencyCode": "USD"
    }
    flight_offers_response = requests.get(amadeus_flight_offers_url, headers=authorization_header, params = flight_offers_request_data)
    
    flight_offers = []
    for flight_offer in flight_offers_response.json()["data"]:
        flight_offer = {
            "AircraftType": flight_offer["itineraries"][0]["segments"][0]["aircraft"]["code"],
            "Airline": flight_offer["itineraries"][0]["segments"][0]["carrierCode"],
            "DepartureTime": departureDate,
            "ArrivalTime": flight_offer["itineraries"][0]["segments"][-1]["arrival"]["at"],
            "Price": flight_offer["price"]["total"]
        }
    flight_offers.append(flight_offer)

    current_session.messages[-1].responses.append(utilities.PossibleFlightsMessage(flight_offers).construct())

    print(json.dumps(flight_offers))
    return "Great! The possible flights have been added to the latest message!"

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

def end_message():
    '''
    execute this if none of the tools are relevant to the input or if there is not enough details to use other tools
    '''
    return "Cool! You have done what you could do! Thank you"

def update_context(conversation_id: str, total_context: str):
    '''
    updates the context string of the entire session

    keep note that the context string is a string that contains all the relevant KEY information that the user has given so far
    so add or remove item as you wish.

    You don't need to update the with the entire conversation chat, jsut the KEY information that is relevant to travel booking like originLocation, departureTime, arrivalTime, personality
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return "A session with the given conversation id does not exist"
    current_session.context = total_context
    return "Nice! You have updated the context. You can move onto other parts using the initial input as the context"

get_today_tool = FunctionTool.from_defaults(get_today)
generate_summary_text_tool = FunctionTool.from_defaults(generate_summary_text)
airport_iata_tool = FunctionTool.from_defaults(get_airport_iata)
add_summary_tool = FunctionTool.from_defaults(add_summary_text)
add_possible_places_tool = FunctionTool.from_defaults(add_possible_places_text)
add_possible_flights_tool = FunctionTool.from_defaults(add_possible_flights_text)
add_possible_places_to_stay_tool = FunctionTool.from_defaults(add_possible_places_to_stay_text)
emit_message_generation_completed_tool = FunctionTool.from_defaults(emit_message_generation_completed)
update_context_tool = FunctionTool.from_defaults(update_context)
end_message_tool = FunctionTool.from_defaults(end_message)

if __name__ == "__main__":
    #print(get_airport_iana("John F Kennedy International Airport"))
    #add_possible_flights_text("JFK", "LAX", "2024-07-25", 1)
    add_possible_places_text("35.6764", 35.6764, 139.6500)