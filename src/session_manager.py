from enum import Enum

from fastapi import WebSocket
import json

class YumeConversationResponseTypes(str, Enum):
    ON_CONNECTED = "on_connected"
    ON_LOADING = "on_loading"
    ON_RESPONSE = "on_response"

class YumeTravelResponse:
    def __init__(self, type: YumeConversationResponseTypes, response: str):
        self.type = type
        self.response = response

    def get_type(self):
        return self.type

    def get_response(self):
        return self.response

    def to_json(self):
        return json.dumps({
            "type": self.type,
            "response": self.response
        })

class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_history(self):
        return "[" + self.role + "]: " + self.content + "\n"

class Session:
    def __init__(self, conversation_id: str, messages: list[Message]):
        self.conversation_id = conversation_id
        self.messages = messages
        self.websocket_connection = None

    def set_websocket_connection(self, websocket_connection: WebSocket):
        self.websocket_connection = websocket_connection

    async def emit_message(self, message: YumeTravelResponse):
        if self.websocket_connection:
            await self.websocket_connection.send_text(message.to_json())

    def get_latest_message(self) -> str:
        if len(self.messages) > 0:
            return self.messages[-1]
        return ""
    
    def get_chat_history(self) -> str:
        chat_history = ""
        for message in self.messages:
            chat_history += message.to_history()
        return chat_history

class SessionController:
    '''
        Controls all the existing sessions
    '''
    def __init__(self):
        self.sessions = []

    def create_session(self, conversation_id: str) -> Session:
        session = Session(conversation_id, [])
        self.sessions.append(session)
        return session
    
    def delete_session(self, conversation_id: str):
        for session in self.sessions:
            if session.conversation_id == conversation_id:
                self.sessions.remove(session)
                return

    def get_session(self, conversation_id: str) -> Session:
        for session in self.sessions:
            if session.conversation_id == conversation_id:
                return session
        return None

    def send_message(self, conversation_id: str, type: YumeConversationResponseTypes, message: str):
        for session in self.sessions:
            if session.conversation_id == conversation_id:
                session.emit_message(YumeTravelResponse(type, message))
                return

    def add_message(self, conversation_id: str, message: str):
        for session in self.sessions:
            if session.conversation_id == conversation_id:
                session.messages.append(message)
                return
    
# Create a global instance of SessionController
session_controller = SessionController()
