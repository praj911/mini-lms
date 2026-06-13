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
from database import get_db, engine, SessionLocal
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

# Seed database with default data if empty
db = SessionLocal()
try:
    if db.query(models.Course).count() == 0:
        seed_data = [
            {
                "course_title": "Introduction to Python",
                "course_description": "Master foundational programming concepts.",
                "lesson_title": "Variables and Data Types",
                "lesson_content": "Variables are placeholders that store data values in memory. Python supports integers for whole numbers, strings for text messages, and floating points for decimal values.",
                "quizzes": [
                    {"question": "Which data type is used for fractional numbers?", "correct_answer": "float"},
                    {"question": "What keyword is used to define a function in Python?", "correct_answer": "def"},
                    {"question": "Which symbol initializes a comment block?", "correct_answer": "#"},
                    {"question": "What is the output of type(True)?", "correct_answer": "bool"},
                    {"question": "Which collection type is immutable?", "correct_answer": "tuple"},
                    {"question": "How do you append an item to a list?", "correct_answer": "append"},
                    {"question": "What operator calculates exponents?", "correct_answer": "**"},
                    {"question": "Which keyword handles exception catching?", "correct_answer": "except"},
                    {"question": "What function reads user keyboard input?", "correct_answer": "input"},
                    {"question": "Which statement breaks out of a loop?", "correct_answer": "break"},
                ]
            },
            {
                "course_title": "Introduction to Web Development",
                "course_description": "Learn the core technologies of the Web.",
                "lesson_title": "Understanding the DOM and HTML",
                "lesson_content": "The Document Object Model (DOM) is a programming interface for web documents. It represents the page so that programs can change the document structure, style, and content. HTML provides the basic structure of sites.",
                "quizzes": [
                    {"question": "Which HTML tag is used for the main heading?", "correct_answer": "h1"},
                    {"question": "What attribute specifies an image source url?", "correct_answer": "src"},
                    {"question": "Which HTML element creates a bulleted list?", "correct_answer": "ul"},
                    {"question": "What does CSS stand for?", "correct_answer": "Cascading Style Sheets"},
                    {"question": "Which tag embeds JavaScript inline?", "correct_answer": "script"},
                    {"question": "What property changes text color in CSS?", "correct_answer": "color"},
                    {"question": "Which tag defines a hyperlink anchor?", "correct_answer": "a"},
                    {"question": "What CSS layout tool uses tracks and grid lines?", "correct_answer": "grid"},
                    {"question": "Which HTML element creates a dropdown selection input?", "correct_answer": "select"},
                    {"question": "What property adds spacing inside an element border?", "correct_answer": "padding"},
                ]
            },
            {
                "course_title": "Artificial Intelligence Foundations",
                "course_description": "Understand basic AI principles.",
                "lesson_title": "Supervised vs Unsupervised Learning",
                "lesson_content": "Supervised learning uses labeled training data, while unsupervised learning deals with unlabeled data, trying to find underlying structures or patterns dynamically.",
                "quizzes": [
                    {"question": "What type of machine learning uses labeled datasets?", "correct_answer": "supervised learning"},
                    {"question": "What is an algorithm's output error called?", "correct_answer": "loss"},
                    {"question": "Which network structure mimics biological neurons?", "correct_answer": "neural network"},
                    {"question": "What is the standard NLP parsing unit?", "correct_answer": "token"},
                    {"question": "Which ML subfield utilizes deep neural networks?", "correct_answer": "deep learning"},
                    {"question": "What term describes a model overfitting training steps?", "correct_answer": "overfitting"},
                    {"question": "Which math branch calculates neural descent steps?", "correct_answer": "calculus"},
                    {"question": "What algorithm type groups unlabeled data items?", "correct_answer": "clustering"},
                    {"question": "Which component acts as the baseline feature vector?", "correct_answer": "embedding"},
                    {"question": "What state is reached when model adjustments stop changing?", "correct_answer": "convergence"},
                ]
            },
            {
                "course_title": "Database Systems & SQL",
                "course_description": "Master structured databases.",
                "lesson_title": "Relational Schemas and Queries",
                "lesson_content": "Relational databases store data in tables with predefined schemas. SQL allows you to fetch, update, insert, and join data across multiple relational boundaries.",
                "quizzes": [
                    {"question": "What does SQL stand for?", "correct_answer": "Structured Query Language"},
                    {"question": "Which command retrieves data rows from a table?", "correct_answer": "SELECT"},
                    {"question": "What key uniquely identifies a specific row?", "correct_answer": "primary key"},
                    {"question": "Which clause filters rows based on a condition?", "correct_answer": "WHERE"},
                    {"question": "What command removes an entire table structure?", "correct_answer": "DROP TABLE"},
                    {"question": "Which constraint prevents duplicate values?", "correct_answer": "UNIQUE"},
                    {"question": "What operation combines rows from multiple tables?", "correct_answer": "JOIN"},
                    {"question": "Which aggregate function counts the total rows?", "correct_answer": "COUNT"},
                    {"question": "What clause groups rows sharing matching attributes?", "correct_answer": "GROUP BY"},
                    {"question": "What property guarantees complete transaction safety?", "correct_answer": "ACID"},
                ]
            },
            {
                "course_title": "JavaScript Fundamentals",
                "course_description": "Deep dive into JS language basics.",
                "lesson_title": "Async Patterns and Promises",
                "lesson_content": "JavaScript is a single-threaded non-blocking runtime. Asynchronous operations are handled using callbacks, promises, and async/await mechanisms to process network and disk routines.",
                "quizzes": [
                    {"question": "Which keyword declares a block-scoped variable?", "correct_answer": "let"},
                    {"question": "What built-in object represents an error statement?", "correct_answer": "Error"},
                    {"question": "Which keyword pauses execution inside an async block?", "correct_answer": "await"},
                    {"question": "What method safely parses a JSON string layout?", "correct_answer": "JSON.parse"},
                    {"question": "Which symbol represents strict equality validation?", "correct_answer": "==="},
                    {"question": "What array method maps item modifications?", "correct_answer": "map"},
                    {"question": "Which function schedules deferred loop executions?", "correct_answer": "setTimeout"},
                    {"question": "What container manages eventual async success states?", "correct_answer": "Promise"},
                    {"question": "Which method logs debugging outputs to screen consoles?", "correct_answer": "console.log"},
                    {"question": "What concept allows inner functions access to outer scopes?", "correct_answer": "closure"},
                ]
            },
            {
                "course_title": "Software Engineering Frameworks",
                "course_description": "Workflows, version control, and design patterns.",
                "lesson_title": "Git Workflow and Systems Architecture",
                "lesson_content": "Git manages branch structures, mergers, and distributed code push routines. Architectures define component communication boundaries and system execution tiers.",
                "quizzes": [
                    {"question": "Which command initializes a local Git tracking folder?", "correct_answer": "git init"},
                    {"question": "What file patterns are bypassed using a .gitignore layout?", "correct_answer": "excluded files"},
                    {"question": "Which command uploads local history chunks to remote servers?", "correct_answer": "git push"},
                    {"question": "What structural pattern uses decoupled micro-services?", "correct_answer": "microservices"},
                    {"question": "Which diagram maps out system state timelines?", "correct_answer": "sequence diagram"},
                    {"question": "What deployment process runs automated test verifications?", "correct_answer": "CI/CD"},
                    {"question": "Which Git command joins history paths together?", "correct_answer": "git merge"},
                    {"question": "What testing tier evaluates individual modules isolated?", "correct_answer": "unit testing"},
                    {"question": "Which agile tool acts as a visual workflow pipeline?", "correct_answer": "kanban board"},
                    {"question": "What layout documentation exposes available REST protocols?", "correct_answer": "OpenAPI Swagger"},
                ]
            }
        ]

        for item in seed_data:
            # Create Course
            course = models.Course(
                title=item["course_title"],
                description=item["course_description"]
            )
            db.add(course)
            db.commit()
            db.refresh(course)

            # Create Lesson under Course
            lesson = models.Lesson(
                course_id=course.id,
                title=item["lesson_title"],
                content=item["lesson_content"]
            )
            db.add(lesson)
            db.commit()
            db.refresh(lesson)

            # Create Quizzes under Lesson
            for quiz_item in item["quizzes"]:
                quiz = models.Quiz(
                    lesson_id=lesson.id,
                    question=quiz_item["question"],
                    correct_answer=quiz_item["correct_answer"]
                )
                db.add(quiz)
            db.commit()
finally:
    db.close()

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
