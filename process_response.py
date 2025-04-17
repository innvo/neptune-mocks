import json
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.generate.neptune.gremlinTest import transform_gremlin_response

# Load the response from file
with open("neptune_response.json") as f:
    gremlin_response = json.load(f)

# Transform the response
cleaned = transform_gremlin_response(gremlin_response)

# Print the cleaned output
print(json.dumps(cleaned, indent=2)) 