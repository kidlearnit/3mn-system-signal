#!/usr/bin/env python3
"""
Security Check Script
Scans code for potential security issues before commit
"""

import os
import re
import sys
from pathlib import Path

# Patterns to detect sensitive data
SENSITIVE_PATTERNS = [
    r'password\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
    r'key\s*=\s*["\'][^"\']+["\']',
    r'api_key\s*=\s*["\'][^"\']+["\']',
    r'private_key\s*=\s*["\'][^"\']+["\']',
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
]

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    '.git/',
    '__pycache__/',
    '.env.template',
    'SECURITY.md',
    'security_check.py',
    'obfuscate_code.py'
]

def should_exclude_file(file_path):
    """Check if file should be excluded from scanning"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path):
            return True
    return False

def scan_file(file_path):
    """Scan a single file for sensitive data"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern in SENSITIVE_PATTERNS:
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's a placeholder
                        if any(placeholder in match.lower() for placeholder in ['your_', 'placeholder', 'example', 'template']):
                            continue
                        
                        issues.append({
                            'file': str(file_path),
                            'line': i,
                            'content': line.strip(),
                            'match': match,
                            'pattern': pattern
                        })
    
    except Exception as e:
        print(f"⚠️  Error scanning {file_path}: {e}")
    
    return issues

def scan_directory(directory):
    """Scan directory for sensitive data"""
    all_issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_exclude_file(file_path):
                continue
            
            # Only scan text files
            if file_path.suffix in ['.py', '.js', '.html', '.yml', '.yaml', '.json', '.md', '.txt', '.sh', '.bat']:
                issues = scan_file(file_path)
                all_issues.extend(issues)
    
    return all_issues

def main():
    """Main security check function"""
    print("🔍 Security Check Tool")
    print("=" * 50)
    
    # Scan current directory
    issues = scan_directory('.')
    
    if issues:
        print(f"❌ Found {len(issues)} potential security issues:")
        print()
        
        for issue in issues:
            print(f"📁 File: {issue['file']}")
            print(f"📍 Line: {issue['line']}")
            print(f"🔍 Match: {issue['match']}")
            print(f"📝 Content: {issue['content']}")
            print("-" * 50)
        
        print("\n🚨 Security Issues Detected!")
        print("Please review and remove sensitive data before committing.")
        return 1
    else:
        print("✅ No security issues detected!")
        print("Safe to commit.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
