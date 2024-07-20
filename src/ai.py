'''the script that handles the interaction with ai'''

import session_manager

async def handle_query(current_session: session_manager.Session, user_query: str):
    # TO BE IMPLEMENTED
    await current_session.emit_message(
        session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_LOADING, "Trying to load result right now")
        )
    print("Hello World")

async def on_generation_complete(conversation_id: str, response: str):
    current_session = session_manager.session_controller.get_session(conversation_id)
    if current_session == None:
        return
    await current_session.emit_message(session_manager.YumeTravelResponse(session_manager.YumeConversationResponseTypes.ON_RESPONSE, response))