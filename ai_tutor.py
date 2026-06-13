# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

from database import get_db
import models

router = APIRouter(prefix="/ai-tutor", tags=["AI Tutor"])

# Initialize Gemini Client.
# If GEMINI_API_KEY is not in env, genai.Client() raises ValueError.
# We wrap this to prevent crashing the entire application during startup.
try:
    client = genai.Client()
except Exception:
    client = None


class AskQuestionRequest(BaseModel):
    lesson_id: int
    question: str


class AskQuestionResponse(BaseModel):
    response: str


@router.post("/ask", response_model=AskQuestionResponse)
def ask_ai_tutor(payload: AskQuestionRequest, db: Session = Depends(get_db)):
    """
    Asks the AI Tutor a question based on a specific lesson's content.
    """
    global client

    # Try to initialize the client if it wasn't initialized at startup (e.g., if API key was set post-startup)
    if client is None:
        try:
            client = genai.Client()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API Client is not configured. Please set the GEMINI_API_KEY environment variable."
            )

    # Look up the lesson in the database
    lesson = db.query(models.Lesson).filter(models.Lesson.id == payload.lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Set up system instruction using the lesson content
    system_instruction = (
        "You are an expert academic AI Tutor for a Learning Management System. "
        "Use the following lesson content to answer the student's question accurately, "
        f"clearly, and concisely. Lesson Content: {lesson.content or 'No content provided.'}"
    )

    try:
        # Call generate_content with gemini-2.5-flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=payload.question,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response from AI Tutor: {str(e)}"
        )
