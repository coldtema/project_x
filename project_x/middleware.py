def simple_middleware(get_response):
    def middleware(request):
        print("is_secure:", request.is_secure())
        print("X-Forwarded-Proto:", request.META.get("HTTP_X_FORWARDED_PROTO"))
        return get_response(request)
    return middleware