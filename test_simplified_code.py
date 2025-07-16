#!/usr/bin/env python3
"""
Test script to verify the simplified Neptune person nodes generator.
"""

import os
import sys
import tempfile

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generate.gremlin.nodes.neptune_person_nodes_gremlin import (
    generate_person_record,
    generate_batch,
    save_to_csv,
    estimate_optimal_batch_size,
    MAX_FILE_SIZE_BYTES,
    SAFETY_MARGIN
)

def test_single_record():
    """Test single record generation"""
    print("🧪 Testing single record generation...")
    
    record = generate_person_record()
    
    # Check required fields
    required_fields = ['~id', 'node_id:String', 'node_name:String', 'name_full:String', 
                      'date_of_birth:Date', 'anumber_primary:String', '~label']
    
    for field in required_fields:
        if field not in record:
            print(f"   ❌ Missing required field: {field}")
            return False
    
    print(f"   ✅ All required fields present")
    print(f"   📝 Sample record: {record}")
    
    return True

def test_batch_generation():
    """Test batch generation"""
    print("\n🧪 Testing batch generation...")
    
    batch_size = 10
    batch = generate_batch(batch_size)
    
    if len(batch) != batch_size:
        print(f"   ❌ Expected {batch_size} records, got {len(batch)}")
        return False
    
    print(f"   ✅ Generated {len(batch)} records successfully")
    
    # Check first record structure
    first_record = batch[0]
    if not all(field in first_record for field in ['~id', 'node_name:String', '~label']):
        print(f"   ❌ Invalid record structure")
        return False
    
    print(f"   ✅ Record structure is valid")
    
    return True

def test_csv_saving():
    """Test CSV saving functionality"""
    print("\n🧪 Testing CSV saving...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_output_path = os.path.join(temp_dir, "test_batch.csv")
        
        # Generate a small batch
        batch = generate_batch(5)
        
        # Define column order
        column_order = ['~id', 'node_id:String', 'node_name:String', 'name_full:String', 
                       'date_of_birth:Date', 'anumber_primary:String', '~label']
        
        # Save to CSV
        file_size = save_to_csv(batch, test_output_path, column_order)
        
        # Check if file exists and has content
        if not os.path.exists(test_output_path):
            print(f"   ❌ CSV file not created")
            return False
        
        # Check file size
        if file_size <= 0:
            print(f"   ❌ CSV file is empty")
            return False
        
        print(f"   ✅ CSV file created successfully (Size: {file_size} bytes)")
        
        # Read and verify content
        with open(test_output_path, 'r') as f:
            lines = f.readlines()
            if len(lines) != 6:  # 5 records + 1 header
                print(f"   ❌ Expected 6 lines (5 records + header), got {len(lines)}")
                return False
        
        print(f"   ✅ CSV content verified ({len(lines)} lines)")
        
        return True

def test_optimal_batch_calculation():
    """Test optimal batch size calculation"""
    print("\n🧪 Testing optimal batch size calculation...")
    
    optimal_batch_size = estimate_optimal_batch_size()
    
    if optimal_batch_size <= 0:
        print(f"   ❌ Invalid optimal batch size: {optimal_batch_size}")
        return False
    
    # Check if it's reasonable (should be large enough for 2.5GB)
    min_expected = 1000000  # At least 1M records
    if optimal_batch_size < min_expected:
        print(f"   ⚠️  Optimal batch size ({optimal_batch_size:,}) seems small for 2.5GB")
    
    print(f"   ✅ Optimal batch size: {optimal_batch_size:,}")
    
    return True

def test_constants():
    """Test that constants are properly defined"""
    print("\n🧪 Testing constants...")
    
    if MAX_FILE_SIZE_BYTES != 2.5 * 1024 * 1024 * 1024:
        print(f"   ❌ MAX_FILE_SIZE_BYTES is incorrect")
        return False
    
    if SAFETY_MARGIN != 0.9:
        print(f"   ❌ SAFETY_MARGIN is incorrect")
        return False
    
    print(f"   ✅ Constants are properly defined")
    print(f"   📊 Max file size: {MAX_FILE_SIZE_BYTES / (1024**3):.1f} GB")
    print(f"   📊 Safety margin: {SAFETY_MARGIN * 100:.0f}%")
    
    return True

def main():
    """Main test function"""
    print("🚀 Testing simplified Neptune person nodes generator...")
    print("=" * 60)
    
    tests = [
        test_single_record,
        test_batch_generation,
        test_csv_saving,
        test_optimal_batch_calculation,
        test_constants
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"   ❌ Test failed")
        except Exception as e:
            print(f"   ❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📋 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Simplified code is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 