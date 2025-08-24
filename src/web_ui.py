"""Simple web interface for Dakota content generation"""

from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import asyncio
import uuid
import os
from datetime import datetime

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.agents.dakota_agents.orchestrator_with_data import DakotaOrchestratorWithData

app = FastAPI(title="Dakota Content Generator")

# Store job status
jobs = {}

class GenerationRequest(BaseModel):
    topic: str
    word_count: int = 1750
    audience: str = "Institutional Investors"
    tone: str = "Professional/Educational"
    data_file: Optional[str] = None
    analysis_type: str = "general"

class JobStatus(BaseModel):
    id: str
    status: str
    progress: str
    result: Optional[dict] = None
    error: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def home():
    """Simple web form"""
    return """
    <html>
        <head>
            <title>Dakota Content Generator</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
                .status { margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>Dakota Content Generator</h1>
            <form id="generationForm">
                <div class="form-group">
                    <label for="topic">Topic:</label>
                    <input type="text" id="topic" name="topic" required 
                           placeholder="e.g., Infrastructure Investment Trends 2025">
                </div>
                
                <div class="form-group">
                    <label for="word_count">Word Count:</label>
                    <select id="word_count" name="word_count">
                        <option value="800">Short (800 words)</option>
                        <option value="1750" selected>Standard (1,750 words)</option>
                        <option value="2500">Long (2,500 words)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="data_file">Data File (optional):</label>
                    <input type="file" id="data_file" name="data_file" accept=".csv,.xlsx">
                </div>
                
                <button type="submit">Generate Article</button>
            </form>
            
            <div id="status" class="status" style="display: none;"></div>
            
            <script>
                document.getElementById('generationForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    
                    const formData = new FormData();
                    formData.append('topic', document.getElementById('topic').value);
                    formData.append('word_count', document.getElementById('word_count').value);
                    
                    const fileInput = document.getElementById('data_file');
                    if (fileInput.files.length > 0) {
                        formData.append('data_file', fileInput.files[0]);
                    }
                    
                    const statusDiv = document.getElementById('status');
                    statusDiv.style.display = 'block';
                    statusDiv.innerHTML = 'Starting generation...';
                    
                    try {
                        const response = await fetch('/generate', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        statusDiv.innerHTML = `Job started! ID: ${result.job_id}<br>Checking status...`;
                        
                        // Poll for status
                        const interval = setInterval(async () => {
                            const statusResponse = await fetch(`/status/${result.job_id}`);
                            const status = await statusResponse.json();
                            
                            statusDiv.innerHTML = `Status: ${status.status}<br>Progress: ${status.progress}`;
                            
                            if (status.status === 'completed' || status.status === 'failed') {
                                clearInterval(interval);
                                if (status.status === 'completed') {
                                    statusDiv.innerHTML += `<br><a href="/download/${result.job_id}">Download Article Package</a>`;
                                } else {
                                    statusDiv.innerHTML += `<br>Error: ${status.error}`;
                                }
                            }
                        }, 2000);
                        
                    } catch (error) {
                        statusDiv.innerHTML = `Error: ${error.message}`;
                    }
                });
            </script>
        </body>
    </html>
    """

@app.post("/generate")
async def generate_article(
    background_tasks: BackgroundTasks,
    topic: str,
    word_count: int = 1750,
    data_file: Optional[UploadFile] = File(None)
):
    """Start article generation job"""
    job_id = str(uuid.uuid4())
    
    # Save uploaded file if provided
    data_file_path = None
    if data_file:
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        data_file_path = f"{upload_dir}/{job_id}_{data_file.filename}"
        
        with open(data_file_path, "wb") as f:
            content = await data_file.read()
            f.write(content)
    
    # Create job
    jobs[job_id] = JobStatus(
        id=job_id,
        status="queued",
        progress="Waiting to start...",
        result=None,
        error=None
    )
    
    # Start background task
    background_tasks.add_task(
        run_generation,
        job_id,
        topic,
        word_count,
        data_file_path
    )
    
    return {"job_id": job_id}

async def run_generation(job_id: str, topic: str, word_count: int, data_file_path: Optional[str]):
    """Run article generation in background"""
    try:
        jobs[job_id].status = "running"
        jobs[job_id].progress = "Initializing..."
        
        # Create request
        request = ArticleRequest(
            topic=topic,
            word_count=word_count,
            audience="Institutional Investors",
            tone="Professional/Educational"
        )
        
        # Choose orchestrator
        if data_file_path:
            orchestrator = DakotaOrchestratorWithData()
            task = {
                "request": request,
                "data_file": data_file_path,
                "analysis_type": "general"
            }
        else:
            orchestrator = DakotaOrchestrator()
            task = {"request": request}
        
        # Update progress callback
        def update_progress(phase: str):
            jobs[job_id].progress = phase
        
        # Run generation
        result = await orchestrator.execute(task)
        
        if result.get("success"):
            jobs[job_id].status = "completed"
            jobs[job_id].progress = "Article generated successfully!"
            jobs[job_id].result = result.get("data", {})
        else:
            jobs[job_id].status = "failed"
            jobs[job_id].error = result.get("error", "Unknown error")
            
    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].error = str(e)

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get job status"""
    if job_id in jobs:
        return jobs[job_id]
    return {"error": "Job not found"}

@app.get("/download/{job_id}")
async def download_results(job_id: str):
    """Download generated article package"""
    if job_id not in jobs or jobs[job_id].status != "completed":
        return {"error": "Job not completed"}
    
    # In production, would zip the output folder
    # For now, return the main article
    output_folder = jobs[job_id].result.get("output_folder", "")
    article_path = f"{output_folder}/article.md"
    
    if os.path.exists(article_path):
        return FileResponse(article_path, filename="article.md")
    
    return {"error": "Article not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)