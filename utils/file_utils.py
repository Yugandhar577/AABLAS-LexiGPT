"""
utils/file_utils.py
Helper utilities for document generation and file management.
"""

import os
import uuid
import base64
from pathlib import Path
from typing import Optional


def ensure_generated_dir() -> str:
    """
    Ensure the /generated directory exists for output documents.
    Returns the absolute path to the generated directory.
    """
    project_root = Path(__file__).parent.parent
    generated_dir = project_root / "generated"
    generated_dir.mkdir(exist_ok=True)
    return str(generated_dir)


def generate_unique_filename(extension: str) -> str:
    """
    Generate a unique filename using UUID.
    
    Args:
        extension: File extension (e.g., "pdf", "docx", "xlsx", "pptx")
    
    Returns:
        Filename with UUID: e.g., "abc123def456.pdf"
    """
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{unique_id}.{extension.lstrip('.')}"


def get_full_document_path(filename: str) -> str:
    """
    Get the absolute path for a document in the /generated directory.
    
    Args:
        filename: Name of the file (e.g., "abc123.pdf")
    
    Returns:
        Absolute path to the file
    """
    generated_dir = ensure_generated_dir()
    return os.path.join(generated_dir, filename)


def decode_base64_image(base64_string: str, filename: str = None) -> str:
    """
    Decode a base64 image string and save to a temporary file.
    
    Args:
        base64_string: Base64 encoded image data (with or without data URI prefix)
        filename: Optional output filename. If not provided, generates a unique one.
    
    Returns:
        Absolute path to the saved image file
    """
    # Remove data URI prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    # Decode base64
    image_data = base64.b64decode(base64_string)
    
    # Generate temp image path
    if filename is None:
        filename = generate_unique_filename("png")
    
    temp_dir = ensure_generated_dir()
    image_path = os.path.join(temp_dir, f"temp_{filename}")
    
    # Save image
    with open(image_path, "wb") as f:
        f.write(image_data)
    
    return image_path
