"""
Neptune Mocks - A package for generating mock data for Neptune
"""

__version__ = "0.1.0" 

from neptune_gremlin_converter import convert_gremlin_to_opencypher

# Use the function
convert_gremlin_to_opencypher("input.json", "output_directory") 