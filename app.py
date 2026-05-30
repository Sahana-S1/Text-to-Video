from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import jwt
import shutil
import os

# ------------------ CONFIG ------------------
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)

# ------------------ APP ------------------
app = FastAPI(title="AI Text-to-Video Platform")

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ STATIC FILES ------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ------------------ MODELS ------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class VideoRequest(BaseModel):
    prompt: str
    style: str
    voice: str
    subtitles: bool

    @validator("subtitles", pre=True)
    def parse_subtitles(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return v

# ------------------ AUTH ------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ------------------ ROUTES ------------------
@app.get("/")
def root():
    return {"status": "server running"}

@app.post("/login")
def login(req: LoginRequest):
    # Demo login
    if req.username == "student" and req.password == "student123":
        token = create_access_token({"sub": req.username})
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ------------------ VIDEO GENERATION ------------------
def generate_video_from_text(prompt, style, voice, subtitles, output_path):
    """
    DEMO video generator.
    Replace this with real AI video generation later.
    """
    demo_video = os.path.join(STATIC_DIR, "demo_video.mp4")

    if not os.path.exists(demo_video):
        raise HTTPException(
            status_code=500,
            detail="demo_video.mp4 not found in static folder"
        )

    shutil.copyfile(demo_video, output_path)

@app.post("/generate-video")
def generate_video_endpoint(
    req: VideoRequest,
    user: str = Depends(get_current_user)   # 🔐 JWT protected
):
    video_filename = "generated_video.mp4"
    video_path = os.path.join(STATIC_DIR, video_filename)

    generate_video_from_text(
        prompt=req.prompt,
        style=req.style,
        voice=req.voice,
        subtitles=req.subtitles,
        output_path=video_path
    )

    return {
        "status": "success",
        "video_url": f"/static/{video_filename}",
        "remaining_credits": 5
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
