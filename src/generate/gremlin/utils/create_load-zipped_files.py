#!/usr/bin/env python3
"""
Script to create gzipped versions of Neptune CSV files and move them to temp directory.
This script processes files in src/data/output/neptune/edges and src/data/output/neptune/nodes
and creates compressed versions in src/data/output/neptune/temp.
"""

import os
import gzip
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_gzipped_files():
    """
    Create gzipped versions of all CSV files in edges and nodes directories
    and move them to the temp directory.
    """
    # Define base paths
    base_path = Path("src/data/output/neptune")
    edges_path = base_path / "edges"
    nodes_path = base_path / "nodes"
    temp_path = base_path / "temp"
    
    # Ensure temp directory exists
    temp_path.mkdir(exist_ok=True)
    
    # Process edges directory
    logger.info("Processing edges directory...")
    process_directory(edges_path, temp_path, "edges")
    
    # Process nodes directory
    logger.info("Processing nodes directory...")
    process_directory(nodes_path, temp_path, "nodes")
    
    logger.info("Gzipping and moving files completed successfully!")

def process_directory(source_dir, temp_dir, dir_type):
    """
    Process all CSV files in a directory, create gzipped versions, and move to temp.
    
    Args:
        source_dir (Path): Source directory containing CSV files
        temp_dir (Path): Temporary directory to move gzipped files to
        dir_type (str): Type of directory ('edges' or 'nodes') for logging
    """
    if not source_dir.exists():
        logger.warning(f"Directory {source_dir} does not exist. Skipping.")
        return
    
    csv_files = list(source_dir.glob("*.csv"))
    
    if not csv_files:
        logger.info(f"No CSV files found in {source_dir}")
        return
    
    logger.info(f"Found {len(csv_files)} CSV files in {dir_type} directory")
    
    for csv_file in csv_files:
        try:
            # Create gzipped filename
            gzipped_filename = f"{csv_file.stem}.csv.gz"
            gzipped_path = temp_dir / gzipped_filename
            
            logger.info(f"Processing {csv_file.name}...")
            
            # Create gzipped version
            with open(csv_file, 'rb') as f_in:
                with gzip.open(gzipped_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Get file sizes for comparison
            original_size = csv_file.stat().st_size
            compressed_size = gzipped_path.stat().st_size
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Created {gzipped_filename} "
                       f"({original_size:,} bytes -> {compressed_size:,} bytes, "
                       f"{compression_ratio:.1f}% compression)")
            
        except Exception as e:
            logger.error(f"Error processing {csv_file.name}: {str(e)}")

def main():
    """Main function to execute the gzipping process."""
    try:
        logger.info("Starting Neptune CSV file gzipping process...")
        create_gzipped_files()
        logger.info("Process completed successfully!")
    except Exception as e:
        logger.error(f"An error occurred during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
