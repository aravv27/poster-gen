from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json
import base64
import io
from typing import Optional, Dict
import traceback
from datetime import datetime

# Import your existing modules
from main import Posteragent
from translator import translate_canvas_numbering
from render import WidgetTreeRenderer
from database import DatabaseManager, ProjectStatus, PhaseType
from server_render import RenderDatabase
from server_pydantic import  GenerateRequest,ResultResponse,StatusResponse,GenerateResponse

# ==================== FastAPI App Setup ====================

app = FastAPI(
    title="Poster Generation API",
    description="AI-powered poster generation with multi-phase rendering",
    version="1.0.0"
)

# Configure CORS for Flutter frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "*"],  # Add your Flutter app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize databases
db = DatabaseManager()
render_db = RenderDatabase()

# ==================== Background Task ====================

async def process_poster_generation(job_id: str, prompt: str, width: int, height: int):
    """Background task to generate poster"""
    try:
        print(f"\n{'='*60}")
        print(f"Starting poster generation for job: {job_id}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}\n")
        
        # Step 1: Run the agent through all phases
        print(f"[{job_id}] Phase 1/4: Initializing PosterAgent...")
        agent = Posteragent()
        agent.current_project_id = job_id  # Use the job_id as project_id
        
        print(f"[{job_id}] Phase 2/4: Running multi-phase generation...")
        result_json_str = await agent.create_poster(prompt, project_id=job_id)
        
        # Check if there was an error
        if "Error" in result_json_str or "Failed" in result_json_str:
            print(f"[{job_id}] ❌ Agent failed: {result_json_str}")
            db.update_project_status(job_id, ProjectStatus.FAILED)
            return
        
        # Parse the JSON result
        print(f"[{job_id}] Phase 3/4: Parsing and translating JSON...")
        result_json = json.loads(result_json_str)
        
        # Step 2: Translate the JSON to render engine format
        print(f"[{job_id}] Translating canvas numbering...")
        translated_json = translate_canvas_numbering(result_json)
        
        print(f"[{job_id}] Translated JSON structure:")
        print(json.dumps(translated_json, indent=2))
        
        # Step 3: Render the image
        print(f"[{job_id}] Phase 4/4: Rendering image with WidgetTreeRenderer...")
        renderer = WidgetTreeRenderer(width, height)
        
        # Render to PIL Image instead of file
        from render import WidgetTreeParser, BoxConstraints
        root_widget = WidgetTreeParser.parse(translated_json)
        root_constraints = BoxConstraints(width, width, height, height)
        root_widget.calculate_size(root_constraints)
        final_image = root_widget.render(0, 0, root_constraints)
        
        # Convert RGBA to RGB if needed
        if final_image.mode == 'RGBA':
            from PIL import Image
            background = Image.new('RGB', final_image.size, (255, 255, 255))
            background.paste(final_image, mask=final_image.split()[3])
            final_image = background
        
        # Convert PIL Image to bytes
        print(f"[{job_id}] Converting image to bytes...")
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='PNG', quality=95)
        img_bytes = img_byte_arr.getvalue()
        
        # Step 4: Save to database
        print(f"[{job_id}] Saving image to database...")
        render_db.save_image(
            job_id=job_id,
            image_bytes=img_bytes,
            width=final_image.width,
            height=final_image.height,
            image_format='png'
        )
        
        # Update project status to completed
        db.update_project_status(job_id, ProjectStatus.COMPLETED)
        
        print(f"\n{'='*60}")
        print(f"✅ Poster generation completed for job: {job_id}")
        print(f"Image size: {len(img_bytes)} bytes ({final_image.width}x{final_image.height})")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Error in poster generation for job: {job_id}")
        print(f"Error: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
        print(f"{'='*60}\n")
        
        # Update project status to failed
        db.update_project_status(job_id, ProjectStatus.FAILED)


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Poster Generation API",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_poster(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Start poster generation process (async)
    
    Returns job_id immediately, generation happens in background
    """
    try:
        # Create project in database
        project_id = db.create_project(request.prompt)
        
        # Start background task
        background_tasks.add_task(
            process_poster_generation,
            job_id=project_id,
            prompt=request.prompt,
            width=request.width,
            height=request.height
        )
        
        return GenerateResponse(
            job_id=project_id,
            status="processing",
            message="Poster generation started. Use /api/status/{job_id} to check progress."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get the current status of a poster generation job
    
    Returns progress, current phase, and completion status
    """
    try:
        # Get project from database
        project = db.get_project(job_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = project['status']
        current_phase = project.get('current_phase', 'unknown')
        
        # Calculate progress based on completed phases
        phase_progress = {
            'layout': 25,
            'canvas': 50,
            'background': 75,
            'assets': 100
        }
        
        progress = phase_progress.get(current_phase, 0)
        
        # Check if image is ready
        image_ready = False
        if status == ProjectStatus.COMPLETED:
            image_data = render_db.get_image(job_id)
            image_ready = image_data is not None
            progress = 100
        
        # Create status message
        message_map = {
            ProjectStatus.ACTIVE: f"Processing {current_phase} phase...",
            ProjectStatus.COMPLETED: "Poster generation completed!",
            ProjectStatus.FAILED: "Poster generation failed",
            ProjectStatus.PARTIAL: f"Partially completed (stopped at {current_phase})"
        }
        
        return StatusResponse(
            job_id=job_id,
            status=status,
            current_phase=current_phase,
            progress=progress,
            message=message_map.get(status, "Unknown status"),
            image_ready=image_ready
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")


@app.get("/api/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str, format: str = "base64"):
    """
    Get the final rendered poster image
    
    Parameters:
    - format: 'base64' (returns JSON with base64 image) or 'binary' (returns raw image file)
    """
    try:
        # Check if project exists and is completed
        project = db.get_project(job_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if project['status'] == ProjectStatus.ACTIVE:
            return ResultResponse(
                job_id=job_id,
                status="processing",
                error="Poster is still being generated. Check /api/status/{job_id}"
            )
        
        if project['status'] == ProjectStatus.FAILED:
            return ResultResponse(
                job_id=job_id,
                status="failed",
                error="Poster generation failed"
            )
        
        # Get image from database
        image_data = render_db.get_image(job_id)
        
        if not image_data:
            raise HTTPException(status_code=404, detail="Rendered image not found")
        
        if format == "binary":
            # Return raw image file
            return Response(
                content=image_data['image_data'],
                media_type=f"image/{image_data['image_format']}",
                headers={
                    "Content-Disposition": f"inline; filename=poster_{job_id}.{image_data['image_format']}"
                }
            )
        else:
            # Return base64 encoded image in JSON
            base64_image = base64.b64encode(image_data['image_data']).decode('utf-8')
            
            return ResultResponse(
                job_id=job_id,
                status="completed",
                image=f"data:image/{image_data['image_format']};base64,{base64_image}",
                width=image_data['width'],
                height=image_data['height'],
                file_size=image_data['file_size']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving result: {str(e)}")


@app.get("/api/projects")
async def list_projects(status: Optional[str] = None):
    """
    List all poster generation projects
    
    Optionally filter by status: active, completed, failed, partial
    """
    try:
        if status:
            projects = db.list_projects(ProjectStatus(status))
        else:
            projects = db.list_projects()
        
        return {
            "total": len(projects),
            "projects": projects
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing projects: {str(e)}")


@app.delete("/api/projects/{job_id}")
async def delete_project(job_id: str):
    """
    Delete a project and its rendered image
    """
    try:
        # Check if project exists
        project = db.get_project(job_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete from both databases
        db.delete_project(job_id)
        render_db.delete_image(job_id)
        
        return {
            "message": f"Project {job_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")


@app.get("/api/phases/{job_id}")
async def get_phase_results(job_id: str):
    """
    Get detailed results for each phase of generation
    
    Useful for debugging
    """
    try:
        project = db.get_project(job_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        phases = db.get_all_phase_results(job_id)
        
        return {
            "job_id": job_id,
            "project": project,
            "phases": phases
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving phases: {str(e)}")


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Starting Poster Generation API Server")
    print("="*60)
    print(f"📍 API Docs: http://localhost:8000/docs")
    print(f"📍 Health Check: http://localhost:8000/")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )