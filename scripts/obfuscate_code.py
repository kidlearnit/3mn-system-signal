#!/usr/bin/env python3
"""
Code Obfuscation Script
Makes Python code harder to read while maintaining functionality
"""

import os
import re
import base64
import zlib
from pathlib import Path

def obfuscate_string(text):
    """Obfuscate string using base64 encoding"""
    encoded = base64.b64encode(text.encode()).decode()
    return f"exec(__import__('base64').b64decode('{encoded}').decode())"

def obfuscate_file(file_path, output_path):
    """Obfuscate a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove comments and docstrings
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)
    content = re.sub(r"'''.*?'''", '', content, flags=re.DOTALL)
    
    # Compress and encode
    compressed = zlib.compress(content.encode())
    encoded = base64.b64encode(compressed).decode()
    
    obfuscated = f'''import zlib,base64
exec(zlib.decompress(base64.b64decode("{encoded}")).decode())'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(obfuscated)

def main():
    """Main obfuscation process"""
    print("🔒 Code Obfuscation Tool")
    print("=" * 40)
    
    # Create obfuscated directory
    obfuscated_dir = Path("obfuscated")
    obfuscated_dir.mkdir(exist_ok=True)
    
    # Files to obfuscate (sensitive business logic)
    sensitive_files = [
        "backend/app/services/sma_signal_engine.py",
        "backend/app/services/sma_indicators.py",
        "backend/worker/sma_jobs.py",
        "backend/worker/sma_email_digest.py"
    ]
    
    for file_path in sensitive_files:
        if os.path.exists(file_path):
            output_path = obfuscated_dir / Path(file_path).name
            obfuscate_file(file_path, output_path)
            print(f"✅ Obfuscated: {file_path} -> {output_path}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📁 Obfuscated files saved to: {obfuscated_dir}")
    print("⚠️  Note: This is for demonstration. Use proper obfuscation tools for production.")

if __name__ == "__main__":
    main()
