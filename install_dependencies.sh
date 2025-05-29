#!/bin/bash
# Install required Python packages for MyTenSecondStory

echo "🚀 Installing Python dependencies for MyTenSecondStory..."

# Core Flask dependencies
pip install flask flask-cors

# Google Cloud and Vertex AI
pip install google-cloud-aiplatform vertexai

# Image processing
pip install pillow

# Additional useful packages
pip install pathlib uuid

echo "✅ All dependencies installed!"
echo ""
echo "🔧 Next steps:"
echo "1. Set up Google Cloud authentication"
echo "2. Run the Flask backend"
echo "3. Open the HTML file in your browser"
