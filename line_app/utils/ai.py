import os
from dotenv import load_dotenv
load_dotenv()
from aift import setting
from aift.image.detection import lpr

# Load the AI API key from environment variable
AI_API_KEY = os.getenv('AI_API_KEY')

# Set the API key for the AI service
setting.set_api_key(AI_API_KEY)

# Perform license plate recognition on the image
result = lpr.analyze('../../images/image.jpg', crop=1, rotate=1)

# Print the result
print(result)  # This will show the output of the LPR analysis

