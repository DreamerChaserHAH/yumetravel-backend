from fastapi import FastAPI, WebSocket

import utilities
import session_manager
import ai

app = FastAPI()

@app.get("/")
def read_root():
    return "API is running properly"

@app.get("/create_conversation")
def create_conversation():
    '''
    creates a new conversation session so that server can keep track of individual conversation
    '''
    new_conversation_id = utilities.generate_random_string(20)
    session_manager.session_controller.create_session(new_conversation_id)
    return {"conversation_id": new_conversation_id}

@app.get("/query")
async def query(user_query: str, conversation_id: str):
    '''
    creates a particular query to the AI in response to a particular conversation
    '''
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return {"error": "No such conversation exists"}
    
    await ai.handle_query(current_session, user_query=user_query)
    return {"query": user_query}

@app.websocket("/conversation/{conversation_id}")
async def conversation_endpoint(websocket: WebSocket, conversation_id: str):
    '''
    websocket endpoint to handle the conversation between the user and the AI
    there are three events that will be triggered by the server:
    1. on_connect: when the client connects to the server
    2. on_loading: when the server is processing the data
    3. on_response: when the server completes loading
    '''

    def on_connected():
        websocket.send_text("Connected to the server")
    
    def on_loading():
        websocket.send_text("Server is processing the data")

    def on_response():
        websocket.send_text("Server completed loading")

    await websocket.accept()
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    
    current_session.set_websocket_connection(websocket)
    await current_session.emit_message(session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_CONNECTED, "Connected to the server"))

    while True:
        event = await websocket.receive_text()


# returns the latest message in a particular conversation
@app.get("/message")
async def read_latest_message(conversation_id: str):
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return {"error": "No such conversation exists"}
    return {"message": current_session.get_latest_message()}