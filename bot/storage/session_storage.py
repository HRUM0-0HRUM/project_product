user_sessions = {}

def get_session(user_id):
    return user_sessions.get(user_id)

def create_session(user_id, data):
    user_sessions[user_id] = data
    return user_sessions[user_id]

def update_session(user_id, data):
    if user_id in user_sessions:
        user_sessions[user_id].update(data)
    else:
        user_sessions[user_id] = data
    return user_sessions[user_id]

def delete_session(user_id):
    if user_id in user_sessions:
        del user_sessions[user_id]

def session_exists(user_id):
    return user_id in user_sessions