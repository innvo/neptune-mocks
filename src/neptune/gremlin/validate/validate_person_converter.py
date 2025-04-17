from person_converter import convert_gremlin_to_opencypher
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set up input and output paths
input_file = os.path.join(current_dir, "..", "data", "input", "person_gremlin_10.json")
output_dir = os.path.join(current_dir, "..", "data", "output")

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Convert the file
convert_gremlin_to_opencypher(input_file, output_dir)