#!/usr/bin/env python3
"""
Test code comparison explanations
"""
import sys
sys.path.insert(0, '.')

from app.services.code_comparison_service import compare_code_files

print("=" * 80)
print("TESTING CODE COMPARISON EXPLANATIONS")
print("=" * 80)

# Test code
code_v1 = """def is_palindrome(s):
    s = s.lower().replace(" ", "")
    return s == s[::-1]"""

code_v2 = """def is_palindrome(s):
    if not isinstance(s, str):
        raise ValueError("Input must be string")
    clean = ''.join(c.lower() for c in s if c.isalnum())
    left, right = 0, len(clean) - 1
    while left < right:
        if clean[left] != clean[right]:
            return False
        left += 1
        right -= 1
    return True"""

print("\nInput:")
print(f"  Version A: {len(code_v1)} chars")
print(f"  Version B: {len(code_v2)} chars")

print("\nCalling compare_code_files...")
try:
    result = compare_code_files(
        entities_a=[],
        entities_b=[],
        source_a=code_v1,
        source_b=code_v2,
        filename_a="test_v1.py",
        filename_b="test_v2.py",
        language_a="python",
        language_b="python"
    )
    
    print("\nResults:")
    print(f"\nVersion A Explanation:")
    print(f"  Length: {len(result['version_a_explanation'])} chars")
    print(f"  Content: {result['version_a_explanation'][:200]}...")
    
    print(f"\nVersion B Explanation:")
    print(f"  Length: {len(result['version_b_explanation'])} chars")
    print(f"  Content: {result['version_b_explanation'][:200]}...")
    
    if len(result['version_a_explanation']) > 100 and len(result['version_b_explanation']) > 100:
        print("\n✓ SUCCESS! Explanations generated!")
    else:
        print("\n✗ PROBLEM: Explanations are too short (fallback text)")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
