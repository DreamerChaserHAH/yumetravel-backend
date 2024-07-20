import random
import string
from enum import Enum
import json

def generate_random_string(length: int) -> str:
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

class ConversationalMessageResponseType(str):
    SUMMARY = "summary"
    POSSIBLE_PLACES = "possible_places"
    POSSIBLE_FLIGHTS = "possible_flights"
    POSSIBLE_PLACES_TO_STAY = "possible_places_to_stay"

class ConversationalMessageResponse:
    def __init__(self, type: ConversationalMessageResponseType):
        self.type = type

class SummaryMessage(ConversationalMessageResponse):
    def __init__(self, summary: str):
        super().__init__(ConversationalMessageResponseType.SUMMARY)
        self.content = summary
    
    def to_json(self):
        return json.dumps({
            "type": self.type,
            "content": self.content
        })

class PossiblePlacesMessage(ConversationalMessageResponse):
    def __init__(self, places: list[str]):
        super().__init__(ConversationalMessageResponseType.POSSIBLE_PLACES)
        self.content = places
    
    def to_json(self):
        return {
            "type": self.type,
            "content": list(self.content)
        }
    
class PossibleFlightsMessage(ConversationalMessageResponse):
    def __init__(self, flights: list[str]):
        super().__init__(ConversationalMessageResponseType.POSSIBLE_FLIGHTS)
        self.content = flights
    
    def to_json(self):
        return {
            "type": self.type,
            "content": list(self.content)
        }

class PossiblePlacesToStayMessage(ConversationalMessageResponse):
    def __init__(self, places: list[str]):
        super().__init__(ConversationalMessageResponseType.POSSIBLE_PLACES_TO_STAY)
        self.content = places
    
    def to_json(self):
        return {
            "type": self.type,
            "content": list(self.content)
       }
    
    