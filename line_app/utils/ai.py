import os
import argparse
import io
import tempfile
from PIL import Image
from dotenv import load_dotenv
from aift import setting
from aift.image.detection import lpr

# Load the AI API key from the environment variable
load_dotenv()
AI_API_KEY = os.getenv('AI_API_KEY')

# Set the API key for the AI service
setting.set_api_key(AI_API_KEY)

def preprocess_image(input_path, max_size=(800, 800), quality=85):
    """
    Resize and compress an image in memory.
    
    Args:
        input_path (str): Path to the input image.
        max_size (tuple): Maximum width and height of the resized image.
        quality (int): Compression quality (1-100).
    
    Returns:
        BytesIO: In-memory bytes object of the preprocessed image.
    """
    try:
        with Image.open(input_path) as img:
            # Preserve aspect ratio while resizing
            img.thumbnail(max_size, Image.Resampling.LANCZOS)  # Use LANCZOS for high-quality downscaling
            
            # Save the preprocessed image to an in-memory buffer
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=quality)
            img_bytes.seek(0)  # Reset buffer pointer to the beginning
            return img_bytes
    except Exception as e:
        raise RuntimeError(f"Error preprocessing image: {e}")

def analyze_image(image_bytes):
    """
    Analyze the license plate using the AI service.
    
    Args:
        image_bytes (BytesIO): In-memory image bytes.
    
    Returns:
        list: License plate recognition results.
    """
    try:
        # Write the image bytes to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as temp_file:
            temp_file.write(image_bytes.read())
            temp_file.flush()  # Ensure all data is written
            # Call the lpr.analyze function with the temporary file path
            result = lpr.analyze(temp_file.name, crop=1, rotate=1)
            return result
    except Exception as e:
        raise RuntimeError(f"Error analyzing image: {e}")

# Set up argparse
parser = argparse.ArgumentParser(description="Perform license plate recognition on an image.")
parser.add_argument(
    "-p",
    "--path",
    required=True,
    type=str,
    help="Path to the image file for license plate recognition."
)

# Parse arguments
args = parser.parse_args()

try:
    # Preprocess the image in memory
    preprocessed_image = preprocess_image(args.path)
    # print(f"Image preprocessed successfully.")

    # Analyze the image
    result = analyze_image(preprocessed_image)

    # Ensure the result is a list and process it
    if isinstance(result, list):
        license_plates = [item.get('lpr', 'Unknown') for item in result if isinstance(item, dict)]
        for plate in license_plates:
            print(f"{plate}")
    else:
        print("Unexpected result format. Please check the output of lpr.analyze.")
except Exception as e:
    print(f"Error processing the image: {e}")
    exit(1)  # Exit with non-zero status on error
