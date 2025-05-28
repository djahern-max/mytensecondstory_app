#!/usr/bin/env python3
"""
Flask Backend API for MyTenSecondStory
Connects the web app to your existing AI background generator
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import time
import json
from pathlib import Path
import threading
import uuid

# Import your existing background generator
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from PIL import Image, ImageEnhance

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

class BackgroundAPIService:
    def __init__(self):
        print("🚀 Initializing Background API Service...")
        self.setup_vertex_ai()
        self.output_dir = Path("api_backgrounds")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create static directory for serving images
        self.static_dir = Path("static")
        self.static_dir.mkdir(exist_ok=True)
        
    def setup_vertex_ai(self):
        """Initialize Vertex AI (copied from your existing script)"""
        try:
            project_id = "mytensecondstory-461202"
            vertexai.init(project=project_id, location="us-central1")
            self.image_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
            print("✅ Vertex AI initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Vertex AI: {e}")
            raise

    def enhance_prompt(self, base_prompt, style="professional"):
        """Enhanced prompt generation (from your existing script)"""
        style_modifiers = {
            "professional": "professional, clean, modern, corporate, high-end office environment, minimal, sophisticated lighting, 4K quality",
            "creative": "creative, artistic, vibrant colors, modern design, inspiring workspace, dynamic lighting, contemporary",
            "tech": "futuristic, technology, digital, sleek, modern tech office, LED lighting, minimalist, high-tech",
            "cozy": "warm, cozy, comfortable, home office, natural lighting, wood elements, inviting atmosphere",
            "luxury": "luxury, premium, elegant, high-end, sophisticated, marble, gold accents, executive",
            "medical": "medical office, clean, professional healthcare, modern clinic, sterile, trustworthy",
            "education": "educational, classroom, learning environment, academic, knowledge, professional teaching",
            "finance": "financial office, banking, professional, trustworthy, conservative, established",
        }
        
        modifier = style_modifiers.get(style, style_modifiers["professional"])
        enhanced = f"{base_prompt}, {modifier}, no people, empty space, background only, commercial photography, high quality"
        
        return enhanced

    def generate_background_sync(self, prompt, style="professional"):
        """Generate background synchronously"""
        try:
            enhanced_prompt = self.enhance_prompt(prompt, style)
            print(f"🎨 Generating: {enhanced_prompt}")
            
            # Generate image
            images = self.image_model.generate_images(
                prompt=enhanced_prompt,
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="dont_allow"
            )
            
            if not images:
                raise Exception("No images generated")
            
            # Save the image
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            filename = f"bg_{style}_{timestamp}_{unique_id}.jpg"
            filepath = self.output_dir / filename
            
            # Save original
            images[0].save(location=str(filepath))
            
            # Enhance image
            enhanced_path = self.enhance_image(filepath)
            
            # Copy to static directory for serving
            static_filename = f"bg_{unique_id}.jpg"
            static_path = self.static_dir / static_filename
            
            # Copy enhanced version to static
            if enhanced_path != str(filepath):
                enhanced_img = Image.open(enhanced_path)
            else:
                enhanced_img = Image.open(filepath)
            
            enhanced_img.save(static_path, quality=90, optimize=True)
            
            print(f"✅ Background generated: {static_filename}")
            
            return {
                "success": True,
                "filename": static_filename,
                "url": f"/static/{static_filename}",
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt
            }
            
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def enhance_image(self, image_path):
        """Enhance generated image (from your existing script)"""
        try:
            img = Image.open(image_path)
            
            # Resize to exact video dimensions
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            
            # Enhance contrast and brightness slightly
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)
            
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)
            
            # Save enhanced version
            enhanced_path = str(image_path).replace('.jpg', '_enhanced.jpg')
            img.save(enhanced_path, quality=95, optimize=True)
            
            return enhanced_path
            
        except Exception as e:
            print(f"⚠️ Enhancement failed: {e}")
            return str(image_path)

# Initialize the service
bg_service = BackgroundAPIService()

# Store for async generation tasks
generation_tasks = {}

@app.route('/')
def index():
    """Serve the main web app"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MyTenSecondStory - Loading...</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 MyTenSecondStory</h1>
            <p>Backend API Server is Running!</p>
            <p>📁 Open your HTML file in a browser to use the app</p>
            <p>🔗 API endpoint: <code>/api/generate-background</code></p>
        </div>
    </body>
    </html>
    """)

@app.route('/api/generate-background', methods=['POST'])
def generate_background():
    """API endpoint to generate backgrounds"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'prompt' in request"
            }), 400
        
        prompt = data['prompt'].strip()
        style = data.get('style', 'professional')
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "Empty prompt provided"
            }), 400
        
        print(f"🎨 API Request: {prompt} (style: {style})")
        
        # Generate background synchronously
        result = bg_service.generate_background_sync(prompt, style)
        
        if result['success']:
            # Return full URL for the frontend
            result['imageUrl'] = f"http://localhost:5000{result['url']}"
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/generate-background-async', methods=['POST'])
def generate_background_async():
    """Async version for longer generation times"""
    try:
        data = request.get_json()
        prompt = data['prompt'].strip()
        style = data.get('style', 'professional')
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Store task
        generation_tasks[task_id] = {
            "status": "generating",
            "prompt": prompt,
            "style": style,
            "created_at": time.time()
        }
        
        # Start background generation in thread
        def generate_in_background():
            result = bg_service.generate_background_sync(prompt, style)
            generation_tasks[task_id].update({
                "status": "completed" if result['success'] else "failed",
                "result": result,
                "completed_at": time.time()
            })
        
        threading.Thread(target=generate_in_background, daemon=True).start()
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "status": "generating"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    """Check status of async generation task"""
    if task_id not in generation_tasks:
        return jsonify({
            "success": False,
            "error": "Task not found"
        }), 404
    
    task = generation_tasks[task_id]
    
    if task['status'] == 'completed':
        result = task['result']
        if result['success']:
            result['imageUrl'] = f"http://localhost:5000{result['url']}"
        return jsonify(result)
    elif task['status'] == 'failed':
        return jsonify(task['result']), 500
    else:
        return jsonify({
            "success": True,
            "status": "generating",
            "message": "Background is being generated..."
        })

@app.route('/static/<filename>')
def serve_static(filename):
    """Serve generated background images"""
    return send_from_directory('static', filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "MyTenSecondStory Background API",
        "vertex_ai": "connected",
        "timestamp": time.time()
    })

@app.route('/api/backgrounds')
def list_backgrounds():
    """List all generated backgrounds"""
    try:
        backgrounds = []
        for img_file in Path('static').glob('*.jpg'):
            backgrounds.append({
                "filename": img_file.name,
                "url": f"/static/{img_file.name}",
                "size": img_file.stat().st_size,
                "created": img_file.stat().st_mtime
            })
        
        return jsonify({
            "success": True,
            "backgrounds": sorted(backgrounds, key=lambda x: x['created'], reverse=True)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting MyTenSecondStory Backend API...")
    print("📍 Server will run at: http://localhost:5000")
    print("🎨 Background generation ready!")
    print("📁 Open your HTML file and it will connect to this API")
    print()
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
