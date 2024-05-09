from django.http import HttpRequest


def login_processor(request):
    # Your logic to retrieve data for the context
    data = {
        'current_user': request.user if request.user.is_authenticated else "Anon",
    }
    return data


def filtered_chat_users(request):
    co_workers = ()
    return {"chat_users": co_workers}


def filtered_chat_rooms(request):
    rooms = ()
    return {"chats": rooms}
