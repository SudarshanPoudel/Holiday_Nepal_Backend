from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://localhost:5173', 
        ],
        allow_credentials=True,
        allow_methods=['*'],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=['*'],  # Allows all headers (Authorization, Content-Type, etc.)
    )
