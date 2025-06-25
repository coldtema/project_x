def simple_middleware(get_response):
    def middleware(request):
        print("is_secure:", request.is_secure())
        print(request.META)
        return get_response(request)
    return middleware