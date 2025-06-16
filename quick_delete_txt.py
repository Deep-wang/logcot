#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to quickly delete all .txt files in a specified directory (simplified version)
"""

import os
import glob

def quick_delete_txt_files(directory_path, recursive=False):
    """
    Quickly delete all .txt files in the specified directory
    
    Args:
        directory_path (str): Target directory path
        recursive (bool): Whether to recursively delete .txt files in subdirectories
    """
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory does not exist: {directory_path}")
        return
    
    # Find .txt files
    if recursive:
        pattern = os.path.join(directory_path, "**", "*.txt")
        txt_files = glob.glob(pattern, recursive=True)
    else:
        pattern = os.path.join(directory_path, "*.txt")
        txt_files = glob.glob(pattern)
    
    if not txt_files:
        print(f"📁 No .txt files found in directory '{directory_path}'")
        return
    
    print(f"🔍 Found {len(txt_files)} .txt files, starting deletion...")
    
    deleted_count = 0
    for file_path in txt_files:
        try:
            os.remove(file_path)
            deleted_count += 1
            print(f"✅ Deleted: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ Failed to delete: {os.path.basename(file_path)} - {e}")
    
    print(f"📊 Deletion completed! Successfully deleted {deleted_count} files")

if __name__ == "__main__":
    # Modify the path here to the directory you want to clean
    TARGET_DIRECTORY = "./Find_detect/output_528"  # Default cleanup directory output_528
    
    print("🗑️  Quick .txt File Deletion Tool")
    print(f"📁 Target directory: {TARGET_DIRECTORY}")
    print("-" * 50)
    
    # Delete .txt files in the current directory
    quick_delete_txt_files(TARGET_DIRECTORY, recursive=False)
    
    # If you need to recursively delete .txt files in subdirectories, uncomment the line below
    # quick_delete_txt_files(TARGET_DIRECTORY, recursive=True) 