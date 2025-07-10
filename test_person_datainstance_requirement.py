#!/usr/bin/env python3
"""
Test script to verify that every person has at least 1 datainstance edge.
This script runs the updated generation code and validates the requirement.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
import importlib.util

def run_generation_pipeline():
    """Run the complete generation pipeline to create nodes and edges"""
    print("🚀 Starting generation pipeline...")
    
    # Add src to path for imports
    sys.path.append('src')
    
    try:
        # Step 1: Generate node data
        print("\n1️⃣ Generating node data...")
        from generate.mock.nodes.generate_node_data import generate_node_data
        node_df = generate_node_data()
        
        # Step 2: Generate person data
        print("\n2️⃣ Generating person data...")
        from generate.mock.nodes.generate_mock_person_data_json import generate_mock_person_data
        person_data = generate_mock_person_data()
        
        # Step 3: Generate datainstance data
        print("\n3️⃣ Generating datainstance data...")
        from generate.mock.nodes.generate_mock_datainstance_data_json import generate_mock_datainstance_data
        datainstance_data = generate_mock_datainstance_data()
        
        # Step 4: Generate person-datainstance edges
        print("\n4️⃣ Generating person-datainstance edges...")
        edge_module_path = 'src/generate/mock/edges/generate_mock_person-datainstance_edge.py'
        spec = importlib.util.spec_from_file_location('generate_mock_person_datainstance_edge', edge_module_path)
        edge_module = importlib.util.module_from_spec(spec)
        sys.modules['generate_mock_person_datainstance_edge'] = edge_module
        spec.loader.exec_module(edge_module)
        edge_df = edge_module.generate_person_datainstance_edges()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in generation pipeline: {str(e)}")
        return False

def validate_person_datainstance_requirement():
    """Validate that every person has at least 1 datainstance edge"""
    print("\n🔍 Validating person-datainstance requirement...")
    
    try:
        # Read the generated edge data
        edge_file = Path("src/data/output/gds/mock_person-datainstance_data.json")
        if not edge_file.exists():
            print("❌ Edge data file not found!")
            return False
        
        with open(edge_file, 'r') as f:
            edges = json.load(f)
        
        # Read node data to get all person nodes
        node_df = pd.read_csv('src/data/input/node_data.csv')
        person_nodes = node_df[node_df['node_type'] == 'person']
        
        # Count edges per person
        person_edge_counts = {}
        for edge in edges:
            person_id = edge['node_id_from']
            person_edge_counts[person_id] = person_edge_counts.get(person_id, 0) + 1
        
        # Check for persons with no edges
        persons_with_no_edges = []
        for _, person in person_nodes.iterrows():
            person_id = person['node_id']
            if person_id not in person_edge_counts or person_edge_counts[person_id] == 0:
                persons_with_no_edges.append(person_id)
        
        # Print results
        total_persons = len(person_nodes)
        persons_with_edges = total_persons - len(persons_with_no_edges)
        
        print(f"\n📊 Validation Results:")
        print(f"Total persons: {total_persons}")
        print(f"Persons with at least 1 datainstance edge: {persons_with_edges}")
        print(f"Persons with no datainstance edges: {len(persons_with_no_edges)}")
        
        # Edge distribution
        edge_distribution = {}
        for count in person_edge_counts.values():
            edge_distribution[count] = edge_distribution.get(count, 0) + 1
        
        print(f"\n📈 Edge Distribution:")
        for count in sorted(edge_distribution.keys()):
            print(f"Persons with {count} datainstance edge(s): {edge_distribution[count]}")
        
        # Final validation
        if len(persons_with_no_edges) == 0:
            print(f"\n✅ SUCCESS: Every person has at least 1 datainstance edge!")
            return True
        else:
            print(f"\n❌ FAILURE: {len(persons_with_no_edges)} persons have no datainstance edges")
            print("Persons without edges:", persons_with_no_edges[:5])  # Show first 5
            return False
            
    except Exception as e:
        print(f"❌ Error in validation: {str(e)}")
        return False

def main():
    """Main function to run the test"""
    print("🧪 Testing Person-DataInstance Requirement")
    print("=" * 50)
    
    # Run generation pipeline
    success = run_generation_pipeline()
    if not success:
        print("❌ Generation pipeline failed!")
        return False
    
    # Validate requirement
    requirement_met = validate_person_datainstance_requirement()
    
    if requirement_met:
        print("\n🎉 TEST PASSED: Every person has at least 1 datainstance edge!")
    else:
        print("\n💥 TEST FAILED: Some persons are missing datainstance edges!")
    
    return requirement_met

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 