from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from wsgiref.simple_server import make_server

provider = TracerProvider(
    resource=Resource.create({"service.name": "user-api", "service.version": "0.1.0"})
)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("user-api", "0.1.0")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "")
    with tracer.start_as_current_span("HTTP GET /users/{user_id}") as span:
        span.set_attribute("http.request.method", "GET")
        span.set_attribute("http.route", "/users/{user_id}")
        span.set_attribute("url.scheme", "http")
        user_id = path.rsplit("/", 1)[-1]
        if not user_id.isdigit():
            span.set_attribute("http.response.status_code", 400)
            start_response("400 Bad Request", [("content-type", "text/plain")])
            return [b"user_id must be numeric"]
        with tracer.start_as_current_span("SELECT users") as db_span:
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.operation.name", "SELECT")
            db_span.add_event("db.result", {"row_count": 1})
        span.set_attribute("http.response.status_code", 200)
        start_response("200 OK", [("content-type", "application/json")])
        return [('{"user_id":"%s"}' % user_id).encode()]


if __name__ == "__main__":
    print("Listening on http://127.0.0.1:8080")
    with make_server("127.0.0.1", 8080, app) as server:
        server.serve_forever()
