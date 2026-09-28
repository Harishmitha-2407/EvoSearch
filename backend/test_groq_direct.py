#!/usr/bin/env python3
"""
Direct test of Groq API to see if it's working
"""
import sys
sys.path.insert(0, '.')

from app.config import settings

print("=" * 80)
print("GROQ API DIRECT TEST")
print("=" * 80)

print("\n1. Checking Configuration:")
print(f"   GROQ_API_KEY: {settings.GROQ_API_KEY[:20]}..." if settings.GROQ_API_KEY else "   GROQ_API_KEY: NOT SET")
print(f"   LLM_PROVIDER: {settings.LLM_PROVIDER}")
print(f"   LLM_MODEL: {settings.LLM_MODEL}")

print("\n2. Importing Groq:")
try:
    from groq import Groq
    print("   ✓ groq package imported successfully")
except ImportError as e:
    print(f"   ✗ Failed to import groq: {e}")
    sys.exit(1)

print("\n3. Creating Groq Client:")
try:
    client = Groq(api_key=settings.GROQ_API_KEY)
    print("   ✓ Groq client created successfully")
except Exception as e:
    print(f"   ✗ Failed to create client: {e}")
    sys.exit(1)

print("\n4. Testing Simple API Call:")
try:
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "user", "content": "Say 'Hello from Groq' in exactly those words."}
        ],
        max_tokens=20
    )
    result = response.choices[0].message.content
    print(f"   ✓ API call successful!")
    print(f"   Response: {result}")
except Exception as e:
    print(f"   ✗ API call failed: {e}")
    sys.exit(1)

print("\n5. Testing Code Explanation Call:")
try:
    code = """def add(a, b):
    return a + b"""
    
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {
                "role": "user", 
                "content": f"Explain this Python code in detail:\n\n```python\n{code}\n```"
            }
        ],
        max_tokens=200
    )
    explanation = response.choices[0].message.content
    print(f"   ✓ Code explanation call successful!")
    print(f"   Length: {len(explanation)} characters")
    print(f"   Explanation:\n   {explanation[:200]}...")
except Exception as e:
    print(f"   ✗ Code explanation call failed: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL TESTS PASSED! ✓")
print("=" * 80)
