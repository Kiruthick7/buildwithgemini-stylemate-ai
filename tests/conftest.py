import os
import pytest

# Ensure Vertex AI Enterprise mode is always enabled during tests
os.environ["GOOGLE_CLOUD_PROJECT"] = "qwiklabs-gcp-03-5c279e7dc881"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "true"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GEMINI_MODEL"] = "gemini-3.6-flash"
