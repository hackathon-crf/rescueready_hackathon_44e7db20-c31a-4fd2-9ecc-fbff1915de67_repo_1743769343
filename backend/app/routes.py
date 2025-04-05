from fastapi import FastAPI, APIRouter, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from backend.app.services import test_service
from settings.config import settings
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HF_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-small"

app_router = APIRouter(
    prefix="/api/app",
    tags=["Retrieval QA"],
)

def create_app(root_path: str = "") -> FastAPI:
    """
    Creating a FastAPI instance and registering routes.

    Args:
        root_path: The root path where the API is mounted (e.g., /username/app_name)
    """

    backend_app = FastAPI(
        title="Template App",
        version="1.0.0",
        openapi_version="3.1.0",
        root_path=root_path
    )

    # CORS Configuration
    backend_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Registering routes
    backend_app.include_router(app_router)
    return backend_app

@app_router.get("/test/")
async def test():
        return {
            "status:": 200,
            "message": test_service(),
            "data": {
                "title": "here is some example data",
                "genAI_info": {
                    "use_cases": ["Chatbot creation", "Content generation", "Data augmentation",
                                  "Customer support automation"],
                    "key_features": {
                        "personalization": "Generates tailored responses based on user input and context.",
                        "RAG_integration": "Utilizes external knowledge sources to enhance generated responses.",
                        "no_code": "Allows non-technical users to build AI-powered chatbots easily.",
                        "security": "Ensures data privacy with secure integrations and compliance."
                    },
                    "user_examples": [
                        {"name": "John", "use_case": "E-commerce chatbot", "result": "Improved customer engagement by 25%"},
                        {"name": "Sara", "use_case": "Content creation",
                         "result": "Saved 10 hours weekly on content production"}
                    ]
                },
                "additional_metrics": {
                    "response_time_ms": 150,
                    "api_version": "1.0.2"
                }
            }
        }

@app_router.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
    audio_data = await file.read()
    response = requests.post(
        HF_API_URL,
        headers=headers,
        data=audio_data,
        params={"language": "fr", "task": "transcribe"}
    )
    if response.status_code == 200:
        return {"text": response.json().get("text", "")}
    else:
        return {"error": f"{response.status_code}: {response.text}"}
    # Registering routes


from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print("ICI")
    user_msg = request.message
    # appelle ton modèle ou autre ici
    return {"response": f"Tu as dit : {user_msg}"}


