import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from neptune.gremlin.util.person_gremlin_result_converter_opencypher_module import convert_gremlin_to_opencypher

def test_conversion():
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the paths
    input_file = os.path.join(current_dir, '..', 'data', 'input', 'person_gremlin_10.json')
    output_dir = os.path.join(current_dir, '..', 'data', 'output')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert the file
    success = convert_gremlin_to_opencypher(input_file, output_dir)
    
    if success:
        print("Conversion completed successfully!")
    else:
        print("Conversion failed!")

if __name__ == "__main__":
    test_conversion()
