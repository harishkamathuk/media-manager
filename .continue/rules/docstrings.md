# Media Manager docstring rules

When generating or revising docstrings in this repository, follow these rules:

## Scope
- Only generate or revise docstrings unless explicitly asked to do more.
- Do not modify executable code, imports, signatures, decorators, or formatting.
- Prefer updating one selected function, method, or class at a time.

## Style
- Use Google-style Python docstrings.
- Keep wording concise, concrete, and conservative.
- Describe observable behavior from the code, not guessed business intent.
- Do not add examples unless explicitly requested.

## Accuracy
- Do not invent side effects, guarantees, exceptions, or return semantics that are not directly supported by the code.
- If intent is ambiguous, describe what the code appears to do in operational terms.
- If a function orchestrates multiple services or depends on broader runtime context, keep the docstring high-level and avoid speculation.

## Content rules
- Include `Args:` only for parameters that are actually present and meaningful.
- Include `Returns:` only when the function returns a meaningful value.
- Include `Raises:` only when exceptions are explicit in the code or clearly implied by direct calls.
- For private helpers, keep docstrings short.
- For public functions and classes, prefer a brief summary plus essential details only.

## Repository-specific guidance
- Prefer terms already used in the codebase and domain.
- Avoid decorative language.
- Avoid repeating type information already obvious from type hints unless it improves clarity.
- For service-layer and orchestration functions, describe coordination responsibilities without overstating certainty.
- For scan, integrity, duplicate, reclaim/bin, and recommendation logic, use the terminology present in the implementation rather than inventing new labels.

## Output discipline
- Return only the requested docstring or docstring revision when asked to generate one.
- If the code is too ambiguous to document safely, say so briefly instead of guessing.