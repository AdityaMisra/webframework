from framework import Response, TemplateResponse, Router

def hello(request, name):
    context = {"greeting": "Hello", "name": name}
    return TemplateResponse("greeting.html", context)

def goodbye(request, name):
    context = {"greeting": "Goodbye", "name": name}
    return TemplateResponse("greeting.html", context)

routes = Router()
routes.add_route(r'/hello/(.*)/$', hello)
routes.add_route(r'/goodbye/(.*)/$', goodbye)


# def hello(request):
#     name = request.args.get('name', 'PyCon')
#     return Response(f"<h1>Hello, {name}</h1>")

def hello(request, name):
    return Response(f"<h1>Hello, {name}</h1>")


def goodbye(request, name):
    return Response(f"<h1>Goodbye, {name}</h1>")


routes = Router()
routes.add_route(r'/hello/(.*)/$', hello)
routes.add_route(r'/goodbye/(.*)/$', goodbye)
