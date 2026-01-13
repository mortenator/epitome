# Claude Code Best Practices

This document outlines best-in-class practices for working with Claude on code projects.

## Table of Contents
- [Project Context: Epitome](#project-context-epitome)
- [Prompt Engineering](#prompt-engineering)
- [Code Generation Guidelines](#code-generation-guidelines)
- [Code Review Practices](#code-review-practices)
- [API Usage Patterns](#api-usage-patterns)
- [File Organization](#file-organization)
- [Error Handling](#error-handling)
- [Testing Strategies](#testing-strategies)
- [Documentation Standards](#documentation-standards)

## Project Context: Epitome

### Overview
**Epitome** is a vertical SaaS platform designed to automate physical production workflows (film, TV, advertising).

**Current Phase**: Phase 1 ("The Utility") — Automating the creation of the Call Sheet.

**Core Problem**: Producers spend ~3.5 hours/day manually formatting Excel files and PDFs.

**Solution**: An "Automated Executive Producer" that ingests natural language prompts (e.g., "3 day shoot for Nike") and raw files (Crew Lists) to instantly generate a production-ready Excel workbook.

### System Architecture

The system follows a linear **Extraction → Transformation → Generation** pipeline:

```
User Input (Prompt + CSV) 
  → Extraction Agent (LLM Parsing)
  → Structured JSON
  → Generator Engine (xlsxwriter)
  → Final Workbook.xlsx
```

#### A. The Input Layer
- **Natural Language Prompt**: e.g., "Create a call sheet for a 3-day shoot in LA starting next Monday."
- **File Attachment (Optional)**: A raw Crew List (CSV/Excel) or Schedule.

#### B. The Extraction Agent (`prompts.py`)
- **Role**: An LLM (Claude/GPT) acts as a "Line Producer."
- **Responsibility**: Normalizes messy inputs into a strict JSON schema.
- **Key Logic**:
  - Calculates relative dates (e.g., "Next Monday").
  - Infers Crew Roles if not explicitly stated.
  - Sets defaults (TBD) for missing critical info.

#### C. The Generator Engine (`production_workbook_generator.py`)
- **Role**: A robust Python script using `xlsxwriter`.
- **Capabilities**:
  - **Dynamic Tab Generation**: Creates 1, 3, or 10 "Call Sheet" tabs based on the `schedule_days` array.
  - **Fallback Templates**: If no crew is provided, pre-populates with standard "Skeleton Crew" roles (Director, DP, Gaffer) so users never receive a blank page.
  - **Styling**: Applies strict "Epitome" branding (Dark Mode headers, specific grid layouts) to match Sample Production files.

### Workbook Structure (Output)

The generated `Epitome_Production_Workbook.xlsx` contains the following sheets, mirroring the uploaded "SAMPLE PRODUCTION WELL" templates:

| Sheet Name | Function | Key Data Points |
|------------|----------|-----------------|
| **Crew List** | Master Contact Database | Role, Name, Phone, Email, Rate, Notes. Grouped by Department. |
| **Call Sheet - Day [X]** | Daily Logistics (Dynamic) | Grid Layout: Production Info, Locations (Shoot/Parking), Weather, Hospital, Crew Call Times, Scene List. |
| **Schedule** | Timeline of Events | Time, Activity/Scene, Notes. |
| **Locations** | Logistics Detail | Name, Address, Contact, Parking Notes, Nearest Hospital. |
| **PO Log** | Financial Tracking | Vendor, Description, Amount, PO#, Budget Code. |

### Data Dictionary & JSON Schema

The Generator expects a JSON object with the following structure:

```json
{
  "production_info": {
    "job_name": "String",
    "client": "String",
    "job_number": "String"
  },
  "logistics": {
    "locations": [
      {
        "name": "String",
        "address": "String",
        "parking": "String"
      }
    ],
    "hospital": {
      "name": "String",
      "address": "String"
    },
    "weather": {
      "high": "String",
      "low": "String",
      "sunrise": "String",
      "sunset": "String"
    }
  },
  "schedule_days": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "crew_call": "07:00 AM",
      "talent_call": "09:00 AM"
    }
  ],
  "crew_list": [
    {
      "department": "Camera",
      "role": "Director of Photography",
      "name": "String",
      "email": "String",
      "rate": "String"
    }
  ]
}
```

### Key Features Implemented

1. **"TBD" Safety Net**: The system handles incomplete data gracefully. Missing locations or times default to "TBD" rather than breaking the script.

2. **Role Normalization**: The system groups crew by department (Production, Camera, G&E, Art, Vanities) to match industry-standard call sheet layouts.

3. **Branded Formatting**:
   - **Header Dark**: `#111827` (Dark Charcoal) with White Text.
   - **Dept Header**: `#D1D5DB` (Light Grey).
   - **Pills/Highlights**: Used for Call Times.

### Development Status & Roadmap

**Current**: `production_workbook_generator.py` is fully functional with mock data.

**Next Steps**:
- Connect the `prompts.py` system prompt to a live LLM endpoint.
- Implement parsing logic for uploaded CSV files to populate `crew_list` dynamically.
- Add "Distribution" layer (Email/SMS logic defined in PRD).

### Working with Claude on Epitome

When asking Claude to work on Epitome code, provide context about:
- The extraction → transformation → generation pipeline
- The expected JSON schema structure
- The xlsxwriter library and workbook formatting requirements
- The "TBD" fallback pattern for missing data
- The Epitome branding guidelines (colors, layout, styling)

## Prompt Engineering

### Clear, Specific Requests
- **Be explicit**: State exactly what you want Claude to do
- **Provide context**: Include relevant code snippets, file paths, and project structure
- **Specify constraints**: Mention language versions, frameworks, style guides, and requirements
- **Break down complex tasks**: Decompose large requests into smaller, manageable steps

### Effective Prompt Structure
```
Context: [Brief description of what you're working on]
Goal: [What you want to achieve]
Constraints: [Any limitations or requirements]
Example: [Reference code or pattern if applicable]
```

### Context Management
- Include relevant file contents when asking about specific code
- Mention the programming language and framework version
- Specify the target environment (browser, Node.js, etc.)
- Provide error messages or logs when debugging

## Code Generation Guidelines

### Request High-Quality Code
- Ask for **production-ready code** with proper error handling
- Request **comments and documentation** for complex logic
- Specify **code style** preferences (ESLint, Prettier, etc.)
- Ask for **type safety** when using TypeScript
- Request **accessibility considerations** for UI code

### Code Patterns to Request
- **Modular architecture**: Functions should be small, focused, and reusable
- **Separation of concerns**: Clear boundaries between layers (UI, business logic, data)
- **SOLID principles**: Especially Single Responsibility and Dependency Inversion
- **DRY (Don't Repeat Yourself)**: Avoid code duplication
- **Consistent naming**: Use clear, descriptive names following project conventions

### Language-Specific Best Practices

#### JavaScript/TypeScript
- Use async/await over callbacks
- Prefer const/let over var
- Use TypeScript for type safety
- Implement proper error handling with try/catch
- Use modern ES6+ features appropriately

#### Python
- Follow PEP 8 style guide
- Use type hints (Python 3.5+)
- Implement proper exception handling
- Use virtual environments
- Document with docstrings

#### React/Next.js
- Use functional components with hooks
- Implement proper state management
- Optimize with useMemo and useCallback when needed
- Handle loading and error states
- Implement proper SEO and accessibility

## Code Review Practices

### Review Checklist
When asking Claude to review code, request checks for:
- **Logic errors** and potential bugs
- **Performance issues** (N+1 queries, unnecessary re-renders, etc.)
- **Security vulnerabilities** (XSS, SQL injection, etc.)
- **Code quality** (readability, maintainability, complexity)
- **Best practices** adherence
- **Test coverage** suggestions

### Refactoring Requests
- Ask for **specific improvements**: "Refactor this function to reduce complexity"
- Request **before/after comparisons**
- Ask for **performance optimizations**
- Request **code simplification** without changing behavior

## API Usage Patterns

### Claude API Integration
```python
# Example: Structured API call pattern
import anthropic

client = anthropic.Anthropic(api_key="your-key")

def get_code_suggestion(prompt: str, context: str) -> str:
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.2,  # Lower for code generation
        system="You are an expert software engineer...",
        messages=[
            {
                "role": "user",
                "content": f"Context: {context}\n\nTask: {prompt}"
            }
        ]
    )
    return message.content[0].text
```

### Best Practices for API Calls
- Use **appropriate temperature**: 0.0-0.3 for code generation, 0.7+ for creative tasks
- Set **reasonable token limits** based on expected output length
- Provide **clear system prompts** that establish Claude's role
- Use **structured output** when available for parsing code
- Implement **error handling** and retry logic
- **Cache responses** when appropriate to reduce API costs

## File Organization

### Request Structured Codebases
When asking Claude to create new code, request:
- **Logical file structure**: Group related functionality
- **Clear separation**: Separate concerns (components, utilities, types, etc.)
- **Consistent naming**: Follow project conventions
- **Import organization**: Group and order imports consistently
- **Barrel exports**: Use index files for clean imports when appropriate

### Example Structure Request
```
Create a feature with:
- components/ - React components
- hooks/ - Custom hooks
- utils/ - Utility functions
- types/ - TypeScript types
- __tests__/ - Test files
- index.ts - Barrel export
```

## Error Handling

### Request Robust Error Handling
Ask Claude to implement:
- **Specific error types**: Custom error classes when appropriate
- **Error boundaries**: In React applications
- **Graceful degradation**: Fallbacks when things go wrong
- **User-friendly messages**: Don't expose technical details to users
- **Logging**: Proper error logging for debugging
- **Recovery strategies**: Retry logic, fallback mechanisms

### Error Handling Patterns
```typescript
// Request patterns like this:
try {
  const result = await riskyOperation();
  return result;
} catch (error) {
  logger.error('Operation failed', { error, context });
  return fallbackValue;
}
```

## Testing Strategies

### Request Comprehensive Tests
Ask Claude to create:
- **Unit tests**: For individual functions and components
- **Integration tests**: For feature interactions
- **Edge case coverage**: Test boundary conditions
- **Mocking strategies**: Proper test isolation
- **Test utilities**: Reusable test helpers

### Test Quality Indicators
- **Clear test names**: Describe what is being tested
- **AAA pattern**: Arrange, Act, Assert
- **No test interdependencies**: Tests should run independently
- **Fast execution**: Avoid slow operations in tests
- **Deterministic**: Tests should produce consistent results

## Documentation Standards

### Request Well-Documented Code
Ask Claude to include:
- **Function documentation**: JSDoc, docstrings, or comments explaining purpose
- **Parameter descriptions**: What each parameter does
- **Return value documentation**: What the function returns
- **Usage examples**: Show how to use the code
- **Edge cases**: Document known limitations or edge cases

### Documentation Patterns

#### JavaScript/TypeScript (JSDoc)
```javascript
/**
 * Calculates the distance between two points in 2D space.
 * 
 * @param {number} x1 - X coordinate of the first point
 * @param {number} y1 - Y coordinate of the first point
 * @param {number} x2 - X coordinate of the second point
 * @param {number} y2 - Y coordinate of the second point
 * @returns {number} The Euclidean distance between the points
 * 
 * @example
 * const distance = calculateDistance(0, 0, 3, 4);
 * console.log(distance); // 5
 */
```

#### Python (Docstrings)
```python
def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate the Euclidean distance between two points in 2D space.
    
    Args:
        x1: X coordinate of the first point
        y1: Y coordinate of the first point
        x2: X coordinate of the second point
        y2: Y coordinate of the second point
    
    Returns:
        The Euclidean distance between the points
    
    Example:
        >>> calculate_distance(0, 0, 3, 4)
        5.0
    """
```

## Advanced Tips

### Iterative Refinement
1. **Start broad**: Ask for initial implementation
2. **Refine incrementally**: Request specific improvements
3. **Add constraints**: Gradually add requirements
4. **Optimize last**: Focus on functionality before optimization

### Context Window Management
- **Summarize large codebases**: Provide overviews rather than full files
- **Focus on relevant sections**: Only include code Claude needs to see
- **Use references**: "See the UserService class for the pattern to follow"
- **Break down large files**: Process in sections if needed

### Prompt Templates

#### Code Generation Template
```
I need to [action] in [language/framework].

Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Constraints:
- [constraint 1]
- [constraint 2]

Please provide:
- [specific deliverable 1]
- [specific deliverable 2]
```

#### Debugging Template
```
I'm encountering an issue with [feature/function].

Error message:
[error message]

Code:
[relevant code]

Expected behavior:
[what should happen]

Actual behavior:
[what actually happens]

Environment:
- Language/Framework: [version]
- OS: [operating system]
- Additional context: [any other relevant info]
```

#### Refactoring Template
```
Please refactor the following code to [goal]:

Current code:
[code snippet]

Goals:
- [improvement 1]
- [improvement 2]

Constraints:
- [must maintain/not break]
- [performance requirement]
```

## Security Considerations

When working with Claude on code, always:
- **Review generated code**: Don't blindly trust AI-generated code
- **Check for vulnerabilities**: Especially when handling user input or external data
- **Validate inputs**: Ensure proper input validation is in place
- **Secure credentials**: Never commit API keys or secrets
- **Follow OWASP guidelines**: For web applications
- **Use prepared statements**: For database queries
- **Implement authentication/authorization**: Where appropriate

## Version Control Integration

### Commit Message Best Practices
When asking Claude to suggest commit messages:
- Use **conventional commits** format: `type(scope): description`
- Make messages **clear and descriptive**
- Reference **issue numbers** when applicable
- Keep **subject line under 50 characters**
- Provide **detailed body** for complex changes

### Code Review Comments
Ask Claude to:
- Provide **constructive feedback**
- Suggest **specific improvements**
- Reference **best practices** and patterns
- Include **code examples** when helpful
- Be **respectful and educational**

## Conclusion

These practices will help you get the most out of Claude for code-related tasks. Remember to:
- Be specific and provide context
- Request production-ready code with proper error handling
- Review all generated code before using it
- Iterate and refine based on results
- Maintain security and quality standards

---

*This document is a living guide and should be updated as best practices evolve.*
