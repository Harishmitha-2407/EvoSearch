"""
Compares code files and generates detailed explanations.
Uses LLM to explain code functionality and changes.
"""
import difflib
import re
from app.services import llm_service

SECURITY_PATTERNS = [
    (re.compile(r"==\s*.*password", re.IGNORECASE), "plain equality comparison near password"),
    (re.compile(r"\bmd5\b", re.IGNORECASE), "MD5 weak hash referenced"),
    (re.compile(r"\bsha1\b", re.IGNORECASE), "SHA-1 weak hash referenced"),
    (re.compile(r"\beval\s*\(", re.IGNORECASE), "eval() usage detected"),
    (re.compile(r"\bexec\s*\(", re.IGNORECASE), "exec() usage detected"),
    (re.compile(r"bcrypt|argon2|pbkdf2", re.IGNORECASE), "Modern password hashing"),
    (re.compile(r"api[_-]?key\s*=\s*['\"]", re.IGNORECASE), "Hardcoded API key detected"),
]


def _security_flags(text: str):
    if not text:
        return []
    flags = []
    for pattern, label in SECURITY_PATTERNS:
        if pattern.search(text):
            flags.append(label)
    return flags


def _generate_code_explanation(source_code: str, language: str, filename: str) -> str:
    """Generate a detailed explanation of what the code does using LLM or heuristics."""
    print(f"[DEBUG] _generate_code_explanation called for {filename}")
    print(f"[DEBUG] LLM available: {llm_service.is_available()}")
    
    if not llm_service.is_available():
        print(f"[DEBUG] LLM not available, generating heuristic explanation")
        return _generate_heuristic_explanation(source_code, language, filename)
    
    try:
        print(f"[DEBUG] Calling LLM for {filename}...")
        prompt = f"""Provide a comprehensive and detailed explanation of this {language} code:

```{language}
{source_code}
```

Explain in detail:
1. What is the overall purpose and functionality of this code?
2. What are all the functions/classes defined and what does each one do specifically?
3. What are the inputs, outputs, and key operations performed?
4. What algorithms or important logic does it implement?
5. What external libraries or dependencies are used?
6. What is the flow of execution?

Be thorough and detailed. This explanation will be used to understand code changes between versions."""

        explanation = llm_service.call_text(
            "You are an expert code documentation specialist. Provide detailed, comprehensive explanations of code functionality.",
            prompt,
            max_tokens=800
        )
        print(f"[DEBUG] LLM response: {len(explanation) if explanation else 0} chars")
        
        if explanation and len(explanation) > 50:
            return explanation
        else:
            print(f"[DEBUG] LLM returned empty/short, using heuristic")
            return _generate_heuristic_explanation(source_code, language, filename)
    except Exception as e:
        print(f"[DEBUG] Exception in LLM call: {e}, using heuristic")
        return _generate_heuristic_explanation(source_code, language, filename)


def _generate_heuristic_explanation(source_code: str, language: str, filename: str) -> str:
    """Generate explanation using heuristics when LLM is unavailable."""
    lines = len(source_code.split('\n')) if source_code else 0
    
    # Extract function/class names
    import re
    
    if language in ['python', 'py']:
        funcs = re.findall(r'def (\w+)\s*\(', source_code)
        classes = re.findall(r'class (\w+)\s*[\(:]', source_code)
    elif language in ['javascript', 'typescript', 'js', 'ts']:
        funcs = re.findall(r'function (\w+)\s*\(|const (\w+)\s*=\s*\(', source_code)
        funcs = [f for f in funcs if f]
        classes = re.findall(r'class (\w+)', source_code)
    else:
        funcs = []
        classes = []
    
    explanation = f"File: {filename} ({language}). {lines} lines of code.\n\n"
    
    if classes:
        explanation += f"Classes defined: {', '.join(set(classes[:5]))}.\n"
    
    if funcs:
        explanation += f"Functions/Methods: {', '.join(set(funcs[:8]))}.\n"
    
    if "import" in source_code.lower() or "require" in source_code.lower():
        explanation += "This file has external dependencies/imports.\n"
    
    if "http" in source_code.lower() or "request" in source_code.lower():
        explanation += "This code appears to handle HTTP requests or network communication.\n"
    
    if "database" in source_code.lower() or "db" in source_code.lower() or "sql" in source_code.lower():
        explanation += "This code includes database operations.\n"
    
    if "async" in source_code or "await" in source_code:
        explanation += "This code uses asynchronous programming patterns.\n"
    
    if "error" in source_code.lower() or "try" in source_code or "except" in source_code or "catch" in source_code:
        explanation += "This code includes error handling.\n"
    
    # Add code snippet
    explanation += f"\nCode snippet:\n{source_code[:300]}..."
    
    return explanation


def _explain_code_change(change_type: str, name: str, before: str, after: str, security_flags: list):
    """Generate detailed explanation focused on WHAT CHANGED and its impact."""
    before_lines = (before or "").split('\n') if before else []
    after_lines = (after or "").split('\n') if after else []
    
    if "ADDED" in change_type:
        purpose = _extract_purpose(after)
        new_lines = len([l for l in after_lines if l.strip()])
        return f"New {name}: Implements {purpose}. {new_lines} lines added to codebase."
    
    elif "REMOVED" in change_type:
        old_lines = len([l for l in before_lines if l.strip()])
        return f"Removed {name}: This {old_lines}-line function/class no longer exists. Functionality deprecated or consolidated elsewhere."
    
    elif "REFACTORED" in change_type:
        old_size = len(before or "")
        new_size = len(after or "")
        percent = int(((new_size - old_size) / max(old_size, 1)) * 100)
        if new_size < old_size:
            return f"Refactored {name}: Code simplified/optimized ({abs(percent)}% more compact) while preserving same logic."
        else:
            return f"Refactored {name}: Code expanded ({percent}% larger) with better structure/clarity, same core behavior."
    
    else:  # MODIFIED
        improvements = _detect_improvements(before, after)
        old_lines = len([l for l in before_lines if l.strip()])
        new_lines = len([l for l in after_lines if l.strip()])
        line_delta = new_lines - old_lines
        
        delta_text = f"{abs(line_delta)} more lines" if line_delta > 0 else f"{abs(line_delta)} fewer lines"
        
        if security_flags:
            security_info = f"Security: {'; '.join(security_flags[:2])}"
            return f"Modified {name}: {security_info}. Implementation change with {delta_text}."
        elif improvements:
            return f"Modified {name}: Enhanced with {improvements}. Code now has {delta_text}."
        else:
            return f"Modified {name}: Implementation changed ({delta_text}). Behavior likely improved or extended."


def _extract_purpose(code_snippet: str) -> str:
    """Extract what the code does in one sentence."""
    if not code_snippet:
        return "functionality"
    
    # Look for docstrings
    import re
    docstring = re.search(r'"""(.*?)"""', code_snippet, re.DOTALL)
    if docstring:
        return docstring.group(1).split('\n')[0][:50]
    
    # Look for comments
    comment = re.search(r'#\s*(.*?)$', code_snippet, re.MULTILINE)
    if comment:
        return comment.group(1)[:50]
    
    # Generic fallback
    if "def " in code_snippet:
        return "a function"
    elif "class " in code_snippet:
        return "a class"
    else:
        return "code logic"


def _detect_improvements(before: str, after: str) -> str:
    """Detect what improved between versions."""
    improvements = []
    
    # Better error handling
    before_try = before.count("try") if before else 0
    after_try = after.count("try") if after else 0
    if after_try > before_try:
        improvements.append("added error handling")
    
    # Better type checking
    if "isinstance" in after and "isinstance" not in before:
        improvements.append("added input validation")
    
    # More efficient (shorter code)
    if len(after) < len(before) * 0.9:
        improvements.append("more efficient code")
    
    # Better comments
    before_comments = (before or "").count("#")
    after_comments = (after or "").count("#")
    if after_comments > before_comments:
        improvements.append("better documentation")
    
    return " & ".join(improvements) if improvements else None


def compare_code_files(entities_a: list[dict], entities_b: list[dict], 
                       source_a: str = "", source_b: str = "",
                       filename_a: str = "", filename_b: str = "",
                       language_a: str = "", language_b: str = "") -> dict:
    """Compare two code versions with detailed explanations."""
    
    print(f"[DEBUG] Starting code comparison. LLM available: {llm_service.is_available()}")
    print(f"[DEBUG] Source A length: {len(source_a)}, Source B length: {len(source_b)}")
    
    # Generate version explanations
    print("[DEBUG] Generating version A explanation...")
    version_a_explanation = _generate_code_explanation(source_a, language_a, filename_a)
    print(f"[DEBUG] Version A explanation length: {len(version_a_explanation)}")
    
    print("[DEBUG] Generating version B explanation...")
    version_b_explanation = _generate_code_explanation(source_b, language_b, filename_b)
    print(f"[DEBUG] Version B explanation length: {len(version_b_explanation)}")
    
    # Generate version summaries
    def get_summary(entities, source):
        type_counts = {}
        for e in entities:
            etype = e.get("entity_type", "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1
        
        lines = len(source.split('\n')) if source else 0
        return {
            "total_entities": len(entities),
            "by_type": type_counts,
            "lines_of_code": lines,
            "overview": f"{len(entities)} entities" if entities else "No structured code"
        }
    
    version_a_summary = get_summary(entities_a, source_a)
    version_b_summary = get_summary(entities_b, source_b)
    
    # Create entity maps
    by_key_a = {}
    for e in entities_a:
        et = "function" if e.get("entity_type") == "method" else e.get("entity_type")
        key = (e.get("parent") or "", et, e.get("name"))
        by_key_a[key] = e
    
    by_key_b = {}
    for e in entities_b:
        et = "function" if e.get("entity_type") == "method" else e.get("entity_type")
        key = (e.get("parent") or "", et, e.get("name"))
        by_key_b[key] = e

    changes = []
    keys_a = set(by_key_a.keys())
    keys_b = set(by_key_b.keys())

    # Added entities
    for key in keys_b - keys_a:
        e = by_key_b[key]
        changes.append({
            "change_type": f"ADDED_{e.get('entity_type', 'ITEM').upper()}",
            "entity_name": e.get("name"),
            "entity_type": e.get("entity_type"),
            "previous_code": None,
            "current_code": e.get("source_snippet") or e.get("signature"),
            "explanation": _explain_code_change(f"ADDED", e.get("name"), "", e.get("source_snippet"), []),
            "category": None,
            "confidence": 0.95,
        })

    # Removed entities
    for key in keys_a - keys_b:
        e = by_key_a[key]
        changes.append({
            "change_type": f"REMOVED_{e.get('entity_type', 'ITEM').upper()}",
            "entity_name": e.get("name"),
            "entity_type": e.get("entity_type"),
            "previous_code": e.get("source_snippet") or e.get("signature"),
            "current_code": None,
            "explanation": _explain_code_change(f"REMOVED", e.get("name"), e.get("source_snippet"), "", []),
            "category": None,
            "confidence": 0.95,
        })

    # Modified entities
    for key in keys_a & keys_b:
        ea, eb = by_key_a[key], by_key_b[key]
        before = (ea.get("source_snippet") or ea.get("signature") or "").strip()
        after = (eb.get("source_snippet") or eb.get("signature") or "").strip()
        
        if before == after:
            continue  # No change
        
        flags = _security_flags(before) + _security_flags(after)
        flags = list(dict.fromkeys(flags))
        
        norm_before = re.sub(r"\s+", " ", before)
        norm_after = re.sub(r"\s+", " ", after)
        similarity = difflib.SequenceMatcher(None, norm_before, norm_after).ratio()
        
        if similarity > 0.85 and not flags:
            change_type = "REFACTORED"
        else:
            change_type = f"MODIFIED_{eb.get('entity_type', 'ITEM').upper()}"
        
        changes.append({
            "change_type": change_type,
            "entity_name": eb.get("name"),
            "entity_type": eb.get("entity_type"),
            "previous_code": before,
            "current_code": after,
            "explanation": _explain_code_change(change_type, eb.get("name"), before, after, flags),
            "category": "security" if flags else None,
            "confidence": 0.95 if flags else round(1 - similarity, 2),
        })

    # Statistics
    stats = {
        "added": sum(1 for c in changes if "ADDED" in c["change_type"]),
        "removed": sum(1 for c in changes if "REMOVED" in c["change_type"]),
        "modified": sum(1 for c in changes if "MODIFIED" in c["change_type"]),
        "refactored": sum(1 for c in changes if c["change_type"] == "REFACTORED"),
        "total_changes": len(changes)
    }

    return {
        "changes": changes,
        "version_a_summary": version_a_summary,
        "version_b_summary": version_b_summary,
        "version_a_explanation": version_a_explanation,
        "version_b_explanation": version_b_explanation,
        "comparison_stats": stats,
        "overall_summary": f"{stats['added']} added, {stats['removed']} removed, {stats['modified']} modified, {stats['refactored']} refactored"
    }
