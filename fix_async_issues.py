#!/usr/bin/env python3
"""
Fix Async Issues Script
Find and fix missing await keywords in service files
"""

import os
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_missing_awaits(file_path):
    """Find lines with missing await keywords."""
    issues = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Look for execute_query calls without await
            if 'execute_query(' in line and 'await' not in line:
                # Check if this is inside an async function
                # Look backwards to find the function definition
                for j in range(i-1, max(0, i-20), -1):
                    if 'async def' in lines[j-1]:
                        issues.append({
                            'line_num': i,
                            'line': line.strip(),
                            'function': lines[j-1].strip()
                        })
                        break
                    elif 'def ' in lines[j-1] and 'async def' not in lines[j-1]:
                        # This is a sync function, skip
                        break
    
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return issues

def main():
    """Find all async issues in service files."""
    service_files = [
        'services/conversation_service.py',
        'services/document_service.py',
        'services/user_service.py',
        'services/session_service.py'
    ]
    
    all_issues = {}
    
    for file_path in service_files:
        if os.path.exists(file_path):
            issues = find_missing_awaits(file_path)
            if issues:
                all_issues[file_path] = issues
    
    # Report findings
    if all_issues:
        print("🔍 Found async issues:")
        print("=" * 60)
        
        for file_path, issues in all_issues.items():
            print(f"\n📄 {file_path}:")
            for issue in issues:
                print(f"  Line {issue['line_num']}: {issue['line']}")
                print(f"    In function: {issue['function']}")
        
        print("\n" + "=" * 60)
        print(f"Total issues found: {sum(len(issues) for issues in all_issues.values())}")
    else:
        print("✅ No async issues found!")

if __name__ == "__main__":
    main()