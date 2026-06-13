# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional

# Local imports
from database import get_db, engine
import models
import auth
from auth import get_current_user, require_role, hash_password, verify_password, create_access_token
import ai_tutor

# Initialize FastAPI App
app = FastAPI(
    title="Mini LMS API",
    description="Backend API for the Mini Learning Management System (LMS)",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

app.mount('/frontend', StaticFiles(directory='frontend', html=True), name='frontend')

# Automatically create database tables on startup
models.Base.metadata.create_all(bind=engine)

# Include the AI Tutor Router
app.include_router(ai_tutor.router)

@app.get('/')
def read_root():
    return FileResponse('frontend/index.html')


# --- Pydantic Schemas for Requests and Responses ---

class UserRegister(BaseModel):
    username: str
    password: str
    role: str  # Must be 'student' or 'teacher'

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class LessonCreate(BaseModel):
    course_id: int
    title: str
    content: Optional[str] = None

class LessonResponse(BaseModel):
    id: int
    course_id: int
    title: str
    content: Optional[str] = None

    class Config:
        from_attributes = True

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int

    class Config:
        from_attributes = True

class QuizCreate(BaseModel):
    question: str
    correct_answer: str

class QuizResponse(BaseModel):
    id: int
    lesson_id: int
    question: str

    class Config:
        from_attributes = True

class QuizSubmission(BaseModel):
    quiz_id: int
    submitted_answer: str

class QuizSubmitResponse(BaseModel):
    correct: bool
    message: str

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    completed: bool

    class Config:
        from_attributes = True


# --- REST API Endpoints ---

# 1. AUTH ENDPOINTS

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new student or teacher in the system.
    """
    if user_data.role not in ["student", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'student' or 'teacher'"
        )

    # Check if username already exists
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered"
        )

    # Hash the password and save
    hashed_pwd = hash_password(user_data.password)
    new_user = models.User(
        username=user_data.username,
        password_hash=hashed_pwd,
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Verifies user credentials and returns a JWT access token.
    """
    user = db.query(models.User).filter(models.User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Generate JWT
    token = create_access_token(data={"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }


# 2. COURSE ENDPOINTS

@app.get("/courses", response_model=List[CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    """
    Fetches all available courses. Open to everyone.
    """
    return db.query(models.Course).all()


@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course_data: CourseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("teacher"))):
    """
    Creates a new course. Restricted to teachers.
    """
    new_course = models.Course(
        title=course_data.title,
        description=course_data.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course


# 3. LESSON ENDPOINTS

@app.get("/courses/{course_id}/lessons", response_model=List[LessonResponse])
def get_lessons(course_id: int, db: Session = Depends(get_db)):
    """
    Fetches all lessons inside a specific course. Open to everyone.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()


@app.post("/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(lesson_data: LessonCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("teacher"))):
    """
    Creates a new lesson inside an existing course. Restricted to teachers.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == lesson_data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated Course not found"
        )

    new_lesson = models.Lesson(
        course_id=lesson_data.course_id,
        title=lesson_data.title,
        content=lesson_data.content
    )
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


# 4. ENROLLMENT ENDPOINT

@app.post("/enroll/{course_id}", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_course(course_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("student"))):
    """
    Enrolls the logged-in student in a course. Restricted to students.
    """
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check for existing enrollment
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == current_user.id,
        models.Enrollment.course_id == course_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course"
        )

    new_enrollment = models.Enrollment(
        user_id=current_user.id,
        course_id=course_id
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment


# 5. QUIZ ENDPOINTS

@app.post("/lessons/{lesson_id}/quiz", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def create_quiz(lesson_id: int, quiz_data: QuizCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("teacher"))):
    """
    Creates a quiz for a lesson. Restricted to teachers.
    Helper endpoint to allow teachers to add quiz questions.
    """
    # Verify lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    new_quiz = models.Quiz(
        lesson_id=lesson_id,
        question=quiz_data.question,
        correct_answer=quiz_data.correct_answer
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    return new_quiz


@app.get("/lessons/{lesson_id}/quiz", response_model=List[QuizResponse])
def get_quiz(lesson_id: int, db: Session = Depends(get_db)):
    """
    Fetches the quiz question(s) for a lesson. Open to everyone.
    Note: The correct answer is excluded from this response for safety.
    """
    # Verify lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    return db.query(models.Quiz).filter(models.Quiz.lesson_id == lesson_id).all()


@app.post("/lessons/{lesson_id}/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(lesson_id: int, submission: QuizSubmission, db: Session = Depends(get_db)):
    """
    Submits a quiz answer and checks if it is correct. Open to everyone.
    """
    # Fetch quiz
    quiz = db.query(models.Quiz).filter(
        models.Quiz.id == submission.quiz_id,
        models.Quiz.lesson_id == lesson_id
    ).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz question not found for this lesson"
        )

    # Case-insensitive comparison with stripped whitespace
    is_correct = submission.submitted_answer.strip().lower() == quiz.correct_answer.strip().lower()
    
    return {
        "correct": is_correct,
        "message": "Correct answer! Well done." if is_correct else "Incorrect answer. Try again!"
    }


# 6. PROGRESS ENDPOINT

@app.post("/lessons/{lesson_id}/complete", response_model=ProgressResponse)
def complete_lesson(lesson_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_role("student"))):
    """
    Marks a lesson as completed for the logged-in student. Restricted to students.
    """
    # Verify lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    # Check if a progress record already exists
    progress = db.query(models.Progress).filter(
        models.Progress.user_id == current_user.id,
        models.Progress.lesson_id == lesson_id
    ).first()

    if progress:
        progress.completed = True
    else:
        progress = models.Progress(
            user_id=current_user.id,
            lesson_id=lesson_id,
            completed=True
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress
