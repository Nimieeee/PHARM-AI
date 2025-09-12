#!/usr/bin/env python3
"""
Emergency fix for persistent Supabase issues
This script applies immediate fixes for the order clause and array issues
"""

import os
import sys
import json
import re

def fix_order_clause_issues():
    """Apply emergency fixes for order clause issues."""
    
    print("🔧 Applying emergency fixes for Supabase issues...")
    
    # Fix 1: Update supabase_manager.py with more robust order handling
    manager_file = 'supabase_manager.py'
    if os.path.exists(manager_file):
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Replace the order handling with a more robust version
        old_order_code = '''                if 'order' in kwargs:
                    original_order = kwargs['order']
                    # Force clean order clause - remove any malformed parts
                    if '.desc.asc' in original_order:
                        clean_order = original_order.replace('.desc.asc', '.desc')
                    elif '.asc.desc' in original_order:
                        clean_order = original_order.replace('.asc.desc', '.asc')
                    else:
                        clean_order = original_order
                    
                    # Ensure proper format
                    if '.' not in clean_order:
                        clean_order = f"{clean_order}.desc"
                    
                    logger.info(f"Order clause processing: {original_order} -> {clean_order}")
                    result = result.order(clean_order)'''
        
        new_order_code = '''                if 'order' in kwargs:
                    order_param = kwargs['order']
                    # Aggressive fix for malformed order clauses
                    clean_order = str(order_param)
                    
                    # Remove any .asc that might be appended incorrectly
                    if clean_order.endswith('.desc.asc'):
                        clean_order = clean_order[:-4]  # Remove .asc
                    elif clean_order.endswith('.asc.desc'):
                        clean_order = clean_order[:-5] + '.asc'  # Keep .asc, remove .desc
                    elif clean_order.endswith('.desc.desc'):
                        clean_order = clean_order[:-5]  # Remove duplicate .desc
                    elif clean_order.endswith('.asc.asc'):
                        clean_order = clean_order[:-4]  # Remove duplicate .asc
                    
                    # Ensure proper format
                    if '.' not in clean_order:
                        clean_order = f"{clean_order}.desc"
                    
                    logger.info(f"Order clause fixed: '{order_param}' -> '{clean_order}'")
                    result = result.order(clean_order)'''
        
        if old_order_code in content:
            content = content.replace(old_order_code, new_order_code)
            with open(manager_file, 'w') as f:
                f.write(content)
            print("✅ Fixed order clause handling in supabase_manager.py")
        else:
            print("⚠️  Order clause code not found in expected format")
    
    # Fix 2: Ensure conversation service handles messages correctly
    conv_file = 'services/conversation_service.py'
    if os.path.exists(conv_file):
        with open(conv_file, 'r') as f:
            content = f.read()
        
        # Ensure messages are always JSON strings for JSONB compatibility
        if "'messages': []," in content:
            content = content.replace("'messages': [],", "'messages': json.dumps([]),")
            print("✅ Fixed messages array format in conversation service")
        
        with open(conv_file, 'w') as f:
            f.write(content)
    
    print("🎉 Emergency fixes applied!")
    print("\n📋 Next steps:")
    print("1. Restart your Streamlit application")
    print("2. Test user creation and conversation loading")
    print("3. Check logs for any remaining issues")

def create_test_script():
    """Create a simple test script to verify fixes."""
    
    test_code = '''#!/usr/bin/env python3
"""
Test script to verify Supabase fixes
Run this after restarting your Streamlit app
"""

def test_order_clauses():
    """Test order clause validation."""
    from supabase_manager import validate_order_clause
    
    test_cases = [
        ('updated_at.desc', 'updated_at.desc'),
        ('added_at.desc.asc', 'added_at.desc'),
        ('created_at.asc.desc', 'created_at.asc'),
        ('name', 'name.desc'),
        ('', 'created_at.desc')
    ]
    
    print("Testing order clause validation:")
    for input_clause, expected in test_cases:
        result = validate_order_clause(input_clause)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_clause}' -> '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    test_order_clauses()
'''
    
    with open('test_fixes.py', 'w') as f:
        f.write(test_code)
    
    print("📝 Created test_fixes.py - run this after restarting your app")

if __name__ == "__main__":
    fix_order_clause_issues()
    create_test_script()