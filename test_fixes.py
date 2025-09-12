#!/usr/bin/env python3
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
