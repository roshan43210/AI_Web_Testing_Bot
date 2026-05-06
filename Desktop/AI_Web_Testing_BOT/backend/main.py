# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import traceback
import os
from backend.crawler import crawl_website
from backend.analyzer import check_links, generate_ai_summary
from backend.database import init_db, save_test_result, get_history, get_test_details

app = FastAPI(title="AI Web Testing Bot")

# Get the absolute path to the frontend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

class TestRequest(BaseModel):
    url: str

@app.get("/")
def home():
    """Serve the frontend index.html"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.get("/index.html")
def serve_index():
    """Serve the main HTML file"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

@app.post("/test")
def test_site(request: TestRequest):
    try:
        url = request.url
        links = crawl_website(url)
        results = check_links(links)
        
        # Generate AI summary
        ai_summary = generate_ai_summary(results, url)
        
        # Save to database
        test_id = save_test_result(url, results)
        
        return {
            "test_id": test_id,
            "total_links": len(links),
            "results": results,
            "ai_summary": ai_summary
        }
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={"error": error_msg, "traceback": tb}
        )

@app.get("/history")
def history(url: str = None, limit: int = 10):
    """Get test history"""
    history = get_history(url, limit)
    return {"history": history}

@app.get("/test/{test_id}")
def get_test(test_id: int):
    """Get specific test result"""
    details = get_test_details(test_id)
    return {"test_id": test_id, "details": details}
