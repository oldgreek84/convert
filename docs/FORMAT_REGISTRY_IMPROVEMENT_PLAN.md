# 🎯 Implementation Plan: Format Registry Design Improvement

## Overview
Transform the current format registry from a simple dictionary-based system into a professional Service Layer + Repository Pattern architecture.

---

## 📋 Phase 1: Foundation (Value Objects & Metadata)

### Goal
Create immutable data structures to represent format information without needing instances.

### 📚 Theory: Value Objects

**What is a Value Object?**
A Value Object is a small, immutable object that represents a descriptive aspect of your domain with no identity. Two value objects are equal if all their attributes are equal.

**Simple Explanation:**
Think of a $5 bill - you don't care which specific $5 bill you have, just that it's worth $5. If you swap it for another $5 bill, nothing changes. That's a value object. Compare this to your passport (an Entity) - swapping it with someone else's passport DOES matter because each has a unique identity.

**Key Properties:**
- **Immutable**: Once created, cannot be changed (use frozen=True in dataclasses)
- **No identity**: Equality based on values, not reference (two FormatMetadata with same values are equal)
- **Side-effect free**: Methods don't modify state, only return new values
- **Replaceable**: Can swap one instance for another with same values

**Why Use Value Objects Here?**
Format metadata (name, extension, description) is descriptive information that doesn't change. A "PDF" format is always "PDF" - it has no lifecycle, no state changes. This makes it perfect for a Value Object.

**Example:**
```python
# Value Object - immutable, compared by value
@dataclass(frozen=True)
class FormatMetadata:
    name: str
    extension: str
    
meta1 = FormatMetadata("pdf", ".pdf")
meta2 = FormatMetadata("pdf", ".pdf")
meta1 == meta2  # True - same values, so equal

# Entity - has identity, compared by ID
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        
user1 = User(1, "John")
user2 = User(1, "John")
user1 == user2  # False - different objects (unless __eq__ overridden)
```

### Tasks
1. **Create `formats/metadata.py`**
   - Define `FormatMetadata` dataclass (frozen=True)
   - Fields: name, display_name, extension, description
   - Add `__str__` method for user-friendly display

2. **Study Concepts**
   - Research: Value Objects in Domain-Driven Design
   - Research: Why immutability matters (frozen dataclasses)
   - Understand: Separation between data and behavior

### Learning Questions
- Why use frozen dataclasses instead of regular classes?
  → *Frozen ensures immutability, prevents accidental modification, makes objects hashable*
- What's the difference between metadata and the actual format instance?
  → *Metadata describes the format (like a book's title page), instance does the actual work (like reading the book)*
- When should you use value objects vs entities?
  → *Use value objects for descriptive attributes without identity; entities for things with unique identity and lifecycle*

---

## 📋 Phase 2: Repository Pattern

### Goal
Extract format storage and retrieval into a dedicated repository class.

### 📚 Theory: Repository Pattern

**What is the Repository Pattern?**
The Repository Pattern provides a collection-like interface for accessing domain objects (like formats), hiding the details of how they're stored (database, dictionary, file, etc.).

**Simple Explanation:**
Think of a library. You don't go directly into the back room to search through boxes - you ask the librarian (repository) "Give me the book about Python". The librarian knows where books are stored and how to find them. You just get your book.

**Key Concepts:**
- **Abstraction**: Hides storage details (could be dict, database, API - caller doesn't care)
- **Collection-like interface**: Methods like `get()`, `add()`, `list_all()` feel like working with a list
- **Single responsibility**: Only handles storage/retrieval, not business logic
- **Centralized queries**: All data access goes through one place

**Repository vs Dictionary:**
```python
# Direct dictionary - spread throughout code
formats = {}
formats['pdf'] = PDFFormat
pdf_class = formats['pdf']  # What if key doesn't exist? Manual error handling everywhere

# Repository - centralized, consistent interface
class FormatRepository:
    def get_class(self, name):
        if name not in self._registry:
            raise UnsupportedFormatError(f"Format '{name}' not found")
        return self._registry[name]

# Now all error handling is in ONE place
```

**Why Separate get_class() and create_instance()?**
- `get_class()`: Returns the class itself (for type checking, inspection)
- `create_instance()`: Factory method that creates AND configures the object
- Principle: Different responsibilities, different methods (Single Responsibility Principle)

**Example:**
```python
# get_class - when you need the type
pdf_class = repository.get_class('pdf')
if issubclass(pdf_class, BaseFormat):  # Type checking
    print("Valid format")

# create_instance - when you need a configured object
pdf_instance = repository.create_instance('pdf', quality=95)
pdf_instance.convert(file)  # Ready to use
```

**Global Instance (Singleton Pattern):**
A singleton ensures only one instance of a class exists. For repositories, this makes sense - you want ONE central registry, not multiple competing ones.

⚠️ **Trade-offs:**
- ✅ Convenient: Access from anywhere
- ✅ Consistent: Everyone sees same data
- ❌ Testing harder: Global state can cause test pollution
- ❌ Coupling: Code depends on global variable

**Solution:** Use dependency injection in tests (pass different repository instance).

### Tasks
1. **Create `formats/repository.py`**
   - Define `FormatRepository` class
   - Implement methods:
     - `register(name, class, display_name, description)`
     - `get_class(name)` - returns class
     - `create_instance(name, **kwargs)` - factory method
     - `get_metadata(name)` - returns metadata without instance
     - `list_all()` - returns all metadata
     - `exists(name)` - check if registered
   
2. **Add Metadata Storage**
   - Store both classes (`_registry`) and metadata (`_metadata`)
   - Populate metadata during registration

3. **Create Global Instance**
   - `repository = FormatRepository()` at module level
   - Understand singleton pattern implications

### Learning Questions
- What is the Repository Pattern and why use it?
  → *Abstraction over data storage; centralizes access, makes storage swappable*
- How does this differ from a simple dictionary?
  → *Adds validation, error handling, metadata management, consistent interface*
- Why separate `get_class()` from `create_instance()`?
  → *Different use cases: inspection vs creation; follows Single Responsibility Principle*
- What are the trade-offs of a global repository instance?
  → *Convenient but can complicate testing; solve with dependency injection*

### Study Materials
- Repository Pattern in Clean Architecture
- Factory Method pattern
- Difference between Factory and Repository

---

## 📋 Phase 3: Service Layer

### Goal
Create business logic layer that uses the repository and provides high-level operations.

### 📚 Theory: Service Layer Pattern

**What is a Service Layer?**
A Service Layer sits between your UI/API and your data storage, containing business logic and orchestrating operations across multiple repositories or domain objects.

**Simple Explanation:**
Imagine ordering food at a restaurant:
- **UI (waiter)**: Takes your order, shows menu
- **Service Layer (chef)**: Knows recipes, combines ingredients, applies cooking rules
- **Repository (pantry)**: Stores and retrieves ingredients

The waiter doesn't know how to cook, and the pantry doesn't know recipes. The chef (service) coordinates everything.

**Key Concepts:**
- **Business logic**: Rules like "can we convert PDF to MOBI?" (not just "does PDF format exist?")
- **Orchestration**: Combines multiple operations (get format, validate, create config)
- **Use case implementation**: Each method is a complete user task
- **Domain language**: Methods named after what users want to do

**Service vs Repository:**

| Aspect | Repository | Service |
|--------|-----------|---------|
| **Purpose** | Store/retrieve data | Implement business rules |
| **Example** | `get_class('pdf')` | `validate_conversion('pdf', 'mobi')` |
| **Knows about** | Storage details | Business rules, workflows |
| **Complexity** | Simple CRUD | Can be complex logic |

**Example:**
```python
# Repository - simple data access
class FormatRepository:
    def get_class(self, name):
        return self._registry[name]  # Just retrieve

# Service - business logic
class FormatService:
    def validate_conversion(self, from_fmt, to_fmt):
        # Business rule: Check both formats exist
        source = self.repository.get_class(from_fmt)
        target = self.repository.get_class(to_fmt)
        
        # Business rule: Check if conversion makes sense
        if from_fmt == 'pdf' and to_fmt == 'mobi':
            # Business knowledge: PDF→MOBI loses quality
            warnings.warn("PDF to MOBI conversion may lose formatting")
        
        # Business rule: Return decision
        return True  # or False based on complex rules
```

**Dependency Injection:**
Instead of `service = FormatService()` creating its own repository inside, we pass repository to constructor: `service = FormatService(repository)`.

**Benefits:**
```python
# Without DI - hard to test
class FormatService:
    def __init__(self):
        self.repo = FormatRepository()  # Fixed dependency!

# With DI - easy to test
class FormatService:
    def __init__(self, repository):
        self.repo = repository  # Can be real or mock!

# In tests:
mock_repo = MockRepository()
service = FormatService(mock_repo)  # Test without real data!
```

**Why Create Target Object in Service?**
Creating a `Target` object involves business rules:
- Which options are valid for this format?
- What defaults should be applied?
- Should warnings be shown?

This is business logic → belongs in Service, not UI.

**Anemic vs Rich Domain Model:**
- **Anemic**: Objects are just data containers, all logic in services
- **Rich**: Objects have behavior (methods that use their data)
- This project uses Rich model (formats have `convert()` method) + Services for orchestration

### Tasks
1. **Create `formats/service.py`**
   - Define `FormatService` class
   - Inject repository via constructor (dependency injection)
   - Implement methods:
     - `get_source_format(name)` - get format, raise error if not found
     - `get_target_format(name, **options)` - get format with options
     - `validate_conversion(from, to)` - check if conversion allowed
     - `list_available_targets(source_format)` - get valid targets
     - `create_target_config(name, category, **options)` - create Target object
     - `get_format_by_extension(ext)` - find format by file extension

2. **Add Error Handling**
   - Use existing exception classes from `exceptions.py`
   - Raise `UnsupportedFormatError` for missing formats
   - Provide helpful error messages

3. **Create Global Service Instance**
   - `format_service = FormatService()`

### Learning Questions
- What is the Service Layer pattern?
  → *Layer containing business logic and orchestration between UI and data storage*
- Why not put this logic in the Repository?
  → *Repository = data access; Service = business rules; different responsibilities*
- What belongs in a service vs a repository?
  → *Service: validation, orchestration, business rules; Repository: CRUD operations*
- How does dependency injection help testing?
  → *Can inject mock dependencies, test without real database/storage*
- Why create a Target object in the service?
  → *Involves business rules (valid options, defaults); service knows domain logic*

### Study Materials
- Service Layer in DDD (Domain-Driven Design)
- Anemic Domain Model vs Rich Domain Model
- Business Logic Layer patterns

---

## 📋 Phase 4: Update Format Registration

### Goal
Enhance the decorator to work with the new repository system.

### 📚 Theory: Decorators with Parameters

**What is a Decorator?**
A decorator is a function that wraps another function/class to add behavior without modifying the original code.

**Simple Explanation:**
Think of gift wrapping. You have a present (your class), and you wrap it (decorate it) with fancy paper (additional behavior). The present stays the same inside, but now it looks different from outside.

**Decorator Without Parameters:**
```python
def register_format(cls):
    """Simple decorator - wraps the class directly"""
    formats_registry[cls.__name__] = cls  # Add behavior
    return cls  # Return unchanged class

@register_format
class PDFFormat:  # When Python sees this, it calls: PDFFormat = register_format(PDFFormat)
    pass
```

**Decorator With Parameters (Closure):**
```python
def register_format(name, display_name=None):
    """Returns a decorator - this is a decorator factory"""
    def decorator(cls):  # The actual decorator
        formats_registry[name] = cls
        metadata[name] = FormatMetadata(name, display_name)
        return cls
    return decorator  # Return the decorator function

@register_format('pdf', display_name='PDF Document')  # Calls register_format() first, THEN decorates
class PDFFormat:
    pass

# What happens:
# 1. register_format('pdf', display_name='PDF Document') is called → returns decorator function
# 2. decorator(PDFFormat) is called → registers the class and returns it
# 3. PDFFormat = result
```

**Key Pattern: Closure**
A closure is when an inner function remembers variables from its outer function:
```python
def outer(name):
    # 'name' is captured in closure
    def inner(cls):
        print(f"Registering {name}")  # Can still access 'name'!
        return cls
    return inner

# 'name' lives on even after outer() finishes
decorator = outer('pdf')  # outer() returns, but 'name' is remembered
decorator(PDFFormat)      # Still knows name='pdf'
```

**Backward Compatibility:**
Why keep old code working when adding new features?
- **Don't break existing code**: Other parts of the project might use old API
- **Gradual migration**: Change one file at a time, not all at once
- **Safety**: If new code has bugs, old code still works

**Example:**
```python
# Old code in converter.py still works:
from formats import get_format
pdf = get_format('pdf')

# New code uses better API:
from formats import format_service
pdf = format_service.get_source_format('pdf')

# Both work! get_format just delegates to repository:
get_format = repository.get_class  # Alias to new implementation
```

### Tasks
1. **Update `formats/__init__.py`**
   - Modify `register_format()` decorator
   - Add optional parameters: `display_name`, `description`
   - Call `repository.register()` instead of direct dictionary assignment
   - Keep decorator returning the class unchanged

2. **Add Backward Compatibility**
   - Export `get_format = repository.get_class`
   - Export `create_format = repository.create_instance`
   - Export `format_service` for new code

3. **Update Format Classes**
   - Add display names and descriptions to `@register_format`
   - Example: `@register_format('pdf', display_name='PDF Document', description='Portable Document Format')`

### Learning Questions
- Why maintain backward compatibility?
  → *Don't break existing code; allows gradual migration; safer refactoring*
- How do decorators with parameters work? (hint: closures)
  → *Decorator factory returns decorator; closure captures parameters; two-level function nesting*
- What's the difference between a decorator with and without parentheses?
  → *Without: decorator gets class directly; With: factory returns decorator, then decorator gets class*

---

## 📋 Phase 5: Refactor CLI UI

### Goal
Update CLI to use the service layer instead of direct format manipulation.

### 📚 Theory: Separation of Concerns & Tell, Don't Ask

**What is Separation of Concerns?**
Different parts of your code should handle different responsibilities. Each module/class should have ONE clear job.

**Simple Explanation:**
Think of building a house:
- **Architect (Service)**: Designs the house, knows building rules
- **Construction worker (UI)**: Follows instructions, builds what's designed
- **Material supplier (Repository)**: Provides bricks, wood, etc.

You don't want the construction worker deciding if the design meets building codes - that's the architect's job!

**Layered Architecture:**
```
┌─────────────────┐
│   UI Layer      │ ← Handles user interaction, displays data
├─────────────────┤
│ Service Layer   │ ← Business logic, validation, orchestration
├─────────────────┤
│ Repository      │ ← Data storage/retrieval
├─────────────────┤
│   Domain        │ ← Core objects (Format classes, value objects)
└─────────────────┘

Dependencies flow DOWNWARD only! UI can call Service, but Service never calls UI.
```

**UI Responsibilities (What should STAY in UI):**
- ✅ Display information to user
- ✅ Get user input
- ✅ Format data for display
- ✅ Handle UI-specific errors (display error messages)

**UI Should NOT:**
- ❌ Know business rules (which conversions are valid)
- ❌ Directly access repositories
- ❌ Create complex domain objects
- ❌ Validate business logic

**Tell, Don't Ask Principle:**

**Bad (Ask):**
```python
# UI asks service for data, then makes decisions
source_format = format_service.get_format('pdf')
target_format = format_service.get_format('mobi')

# UI shouldn't know business rules!
if source_format.can_convert_to(target_format):
    target = Target(name='mobi', ...)  # UI creates complex object
    params_data['target'] = target
```

**Good (Tell):**
```python
# UI tells service what user wants, service handles logic
try:
    target = format_service.create_target_config(
        name='mobi',
        category='ebook',
        quality=95
    )
    params_data['target'] = target  # Just use what service created
except UnsupportedFormatError as e:
    print(f"Error: {e}")  # UI only handles display
```

**Why is Tell, Don't Ask better?**
1. **Business logic in one place**: All rules in service, not scattered in UI
2. **Easier to change**: Change validation rules without touching UI
3. **Easier to test**: Test business logic without UI
4. **Less coupling**: UI doesn't need to know format internals

**Before Refactoring (Bad):**
```python
# UI does too much
formats_dict = get_all_formats()  # Asking for data
for name, cls in formats_dict.items():  # UI iterating storage
    if cls.can_convert_from('pdf'):  # UI checking business rules
        print(name)  # UI making decisions
```

**After Refactoring (Good):**
```python
# UI tells service what it needs
available = format_service.list_available_targets('pdf')  # Tell service what you want
for metadata in available:  # Service returns ready-to-display data
    print(metadata.display_name)  # UI just displays
```

**Improving User Experience:**
Instead of:
```python
print("pdf")  # Raw technical name
```

Show:
```python
print(f"{metadata.display_name} - {metadata.description}")
# "PDF Document - Portable Document Format"
```

Metadata objects make UI code cleaner and more user-friendly!

### Tasks
1. **Refactor `uis/cli_ui.py` - `setup()` method**
   - Import `format_service`
   - Replace `formats.create_format()` with `format_service.get_source_format()`
   - Replace target format creation with `format_service.get_target_format()`
   - Use `format_service.list_available_targets()` for displaying choices
   - Use `format_service.validate_conversion()` to check if conversion is allowed
   - Use `format_service.create_target_config()` to create Target object

2. **Improve User Experience**
   - Display `FormatMetadata` objects instead of raw strings
   - Show format descriptions in selection menu
   - Add better error messages using service exceptions

3. **Remove Direct Dictionary Manipulation**
   - Stop manually setting `params_data['target']`
   - Let the service create the Target object

### Learning Questions
- How does using a service simplify the UI code?
  → *UI delegates business logic; just displays data; less code, fewer bugs*
- What responsibilities should remain in the UI?
  → *User interaction, display formatting, input collection; NOT business rules*
- Why is "Tell, Don't Ask" better than querying objects?
  → *Logic centralized in service; easier to test/change; UI stays simple*

---

## 📋 Phase 6: Add Tests

### Goal
Ensure the new architecture works correctly through comprehensive testing.

### 📚 Theory: Testing Strategies

**What is Unit Testing?**
Testing individual components in isolation to verify they work correctly on their own.

**Simple Explanation:**
Testing is like checking parts of a car:
- **Unit test**: Test the engine separately (does it start?)
- **Integration test**: Test engine + transmission together (do they work together?)
- **End-to-end test**: Test the whole car (can you drive it?)

**Why Test Each Layer Separately?**

**Problem with Testing Everything Together:**
```python
def test_ui():
    ui = CLI()
    ui.setup()  # This calls service, which calls repository, which accesses dict
    # If test fails, where's the bug? UI? Service? Repository? 
```

**Solution - Layered Testing:**
```python
# Test repository alone
def test_repository():
    repo = FormatRepository()
    repo.register('pdf', PDFFormat, 'PDF', 'PDF format')
    assert repo.exists('pdf')  # If fails → bug in repository

# Test service with FAKE repository
def test_service():
    fake_repo = MockRepository()  # Doesn't use real storage
    service = FormatService(fake_repo)
    service.validate_conversion('pdf', 'mobi')
    # If fails → bug in service logic, NOT repository

# Test UI with FAKE service  
def test_ui():
    fake_service = MockFormatService()
    ui = CLI(fake_service)
    # If fails → bug in UI, NOT service or repository
```

**Mocking - Creating Fake Objects for Testing:**

**What is a Mock?**
A fake object that pretends to be a real dependency but is controlled by your test.

**Why Mock?**
1. **Isolation**: Test ONE thing at a time
2. **Speed**: No real database/network calls
3. **Control**: Simulate errors, edge cases
4. **Independence**: Tests don't depend on external systems

**Example - Mock Repository:**
```python
from unittest.mock import Mock

def test_service_handles_missing_format():
    # Create fake repository
    mock_repo = Mock()
    mock_repo.get_class.side_effect = KeyError("Format not found")
    
    # Service uses the mock
    service = FormatService(mock_repo)
    
    # Test that service handles error correctly
    with pytest.raises(UnsupportedFormatError):
        service.get_source_format('unknown')
    
    # Verify repository was called
    mock_repo.get_class.assert_called_once_with('unknown')
```

**Arrange-Act-Assert (AAA) Pattern:**

Every test should have three clear sections:

```python
def test_repository_registration():
    # ARRANGE - Set up test data
    repo = FormatRepository()
    
    # ACT - Perform the action being tested
    repo.register('pdf', PDFFormat, 'PDF Document', 'PDF format')
    
    # ASSERT - Verify the result
    assert repo.exists('pdf')
    assert repo.get_class('pdf') == PDFFormat
```

**Unit vs Integration Tests:**

| Aspect | Unit Test | Integration Test |
|--------|-----------|------------------|
| **Scope** | Single class/function | Multiple components |
| **Dependencies** | Mocked | Real |
| **Speed** | Fast (milliseconds) | Slower (seconds) |
| **Purpose** | Verify logic | Verify components work together |
| **Example** | Test service with mock repo | Test service with real repo |

**Test Pyramid:**
```
        /\
       /  \        Few, slow, expensive
      / E2E \      (whole application)
     /______\
    /        \     More, medium speed
   /Integration\   (multiple components)
  /____________\
 /              \  Many, fast, cheap
/  Unit Tests   \  (single components)
/________________\
```

**Why This Layered Approach?**
If tests fail, you immediately know WHERE the bug is:
- Repository tests fail → Bug in storage logic
- Service tests fail (repo tests pass) → Bug in business logic
- UI tests fail (service tests pass) → Bug in UI code

**Testing Best Practices:**
1. **One assertion per test** (or closely related assertions)
2. **Test name describes what's being tested**: `test_get_source_format_raises_error_for_invalid_format`
3. **Use fixtures** for common setup (pytest fixtures, unittest setUp)
4. **Test edge cases**: empty strings, None, missing data
5. **Don't test implementation details**: Test behavior, not how it's done

**Example Test Suite:**
```python
class TestFormatRepository:
    def test_register_stores_class(self):
        """Test that register() stores the format class"""
        # Arrange
        repo = FormatRepository()
        
        # Act
        repo.register('pdf', PDFFormat, 'PDF', 'PDF format')
        
        # Assert
        assert repo.get_class('pdf') == PDFFormat
    
    def test_get_class_raises_error_for_unknown_format(self):
        """Test that get_class() raises error for missing format"""
        # Arrange
        repo = FormatRepository()
        
        # Act & Assert
        with pytest.raises(UnsupportedFormatError):
            repo.get_class('unknown')
```

### Tasks
1. **Create `tests/test_format_repository.py`**
   - Test format registration
   - Test format retrieval (class and instance)
   - Test metadata storage and retrieval
   - Test non-existent format handling

2. **Create `tests/test_format_service.py`**
   - Test get_source_format with valid/invalid names
   - Test get_target_format with options
   - Test validate_conversion (valid and invalid)
   - Test list_available_targets
   - Test create_target_config
   - Test get_format_by_extension
   - Mock the repository for isolation

3. **Update `tests/test_ui.py`**
   - Test UI with mocked format_service
   - Test error handling

### Learning Questions
- Why test the repository separately from the service?
  → *Isolation finds bugs faster; if service test fails but repo passes, bug is in service*
- How do you mock dependencies in tests?
  → *Use unittest.mock.Mock to create fake objects; control behavior with side_effect, return_value*
- What's the difference between unit tests and integration tests?
  → *Unit: single component, mocked deps, fast; Integration: multiple components, real deps, slower*

### Study Materials
- Mocking in Python (unittest.mock)
- Test-Driven Development (TDD)
- Arrange-Act-Assert pattern

---

## 📋 Phase 7: Optional Enhancements

### Goal
Add advanced features now that the architecture supports them.

### 📚 Theory: Extensibility & Design for Change

**What is Extensibility?**
Designing code so new features can be added easily without breaking existing functionality.

**Simple Explanation:**
Think of a house with electrical outlets. The house was designed with extra outlets and circuit breakers so you can plug in new devices WITHOUT rewiring the entire house. Good software design is similar - plan for future additions.

**Open-Closed Principle (from SOLID):**
"Software entities should be open for extension, but closed for modification"

**Example:**
```python
# BAD - Must modify existing code to add features
def get_format_info(name):
    if name == 'pdf':
        return "PDF format"
    elif name == 'mobi':
        return "Mobi format"
    # Every new format requires changing this function!

# GOOD - Extend without modifying
class FormatMetadata:
    description: str  # Data-driven

# Just add new data, no code changes:
repo.register('pdf', PDFFormat, description='PDF format')
repo.register('mobi', MobiFormat, description='Mobi format')
```

**1. Format Capabilities System**

**Concept:** Instead of hardcoding what each format can do, store capabilities as data.

**Why?**
- **Query capabilities**: "Which formats support images?"
- **Validation**: "Can't convert image-heavy PDF to text-only TXT"
- **User guidance**: "Warning: target format doesn't support images"

**Implementation:**
```python
@dataclass(frozen=True)
class FormatCapabilities:
    supports_images: bool
    supports_metadata: bool
    supports_styles: bool
    is_lossy: bool

@dataclass(frozen=True)
class FormatMetadata:
    name: str
    capabilities: FormatCapabilities
    
# Usage
if not target.capabilities.supports_images:
    warn("Target format will lose images")
```

**2. Conversion Validation Matrix**

**Concept:** Not all conversions are equal. Some are perfect, some lose quality.

**Real-world analogy:**
- Converting DOCX → PDF = excellent (PDF preserves everything)
- Converting PDF → DOCX = poor (PDF doesn't have document structure)
- Converting FB2 → EPUB = excellent (both are ebook formats)
- Converting PDF → MOBI = poor (PDF is fixed-layout, MOBI is reflowable)

**Quality Matrix:**
```python
CONVERSION_MATRIX = {
    ('fb2', 'epub'): {'quality': 'excellent', 'warning': None},
    ('fb2', 'mobi'): {'quality': 'excellent', 'warning': None},
    ('pdf', 'mobi'): {'quality': 'poor', 'warning': 'Layout will be lost'},
    ('pdf', 'txt'): {'quality': 'poor', 'warning': 'All formatting will be lost'},
}

def validate_conversion(from_fmt, to_fmt):
    info = CONVERSION_MATRIX.get((from_fmt, to_fmt))
    if info['quality'] == 'poor':
        print(f"Warning: {info['warning']}")
```

**3. Format Aliases**

**Concept:** Users might use different names for the same format.

**Examples:**
- `jpeg` and `jpg` (same format)
- `epub3` and `epub` (versions of same format)
- `html` and `htm` (file extension variants)

**Implementation:**
```python
class FormatRepository:
    def __init__(self):
        self._registry = {}
        self._aliases = {
            'jpeg': 'jpg',
            'epub3': 'epub',
            'htm': 'html',
        }
    
    def resolve_alias(self, name):
        return self._aliases.get(name, name)
    
    def get_class(self, name):
        canonical_name = self.resolve_alias(name)
        return self._registry[canonical_name]
```

**4. Format Auto-detection (Magic Bytes)**

**Concept:** Don't trust file extensions - read the file to determine its real format.

**Why?**
- User might rename `document.pdf` to `document.txt`
- Downloaded files might have wrong extension
- More robust than relying on filenames

**How it works:**
Every file format has unique starting bytes (magic bytes):
- PDF: `%PDF-1.`
- PNG: `\x89PNG`
- ZIP: `PK\x03\x04`

**Implementation:**
```python
import magic  # python-magic library

def detect_format(file_path):
    mime = magic.from_file(file_path, mime=True)
    # mime = 'application/pdf'
    
    format_map = {
        'application/pdf': 'pdf',
        'application/epub+zip': 'epub',
        'image/jpeg': 'jpg',
    }
    return format_map.get(mime)

# Usage
detected = format_service.detect_format('unknown_file')
print(f"This is actually a {detected} file")
```

**5. Configuration Presets**

**Concept:** Common conversion tasks deserve one-click configurations.

**User Story:**
"I want to convert books for my Kindle" → Should auto-configure for Kindle specs (MOBI format, 6-inch screen, specific DPI)

**Implementation:**
```python
PRESETS = {
    'kindle_optimized': {
        'format': 'mobi',
        'screen_width': 600,
        'screen_height': 800,
        'dpi': 167,
    },
    'high_quality_pdf': {
        'format': 'pdf',
        'quality': 100,
        'compression': False,
    },
}

def apply_preset(preset_name):
    config = PRESETS[preset_name]
    return format_service.create_target_config(**config)
```

**Balancing Simplicity vs Features:**

**When to add a feature:**
- ✅ Solves real user problems
- ✅ Fits naturally into existing architecture
- ✅ Used frequently
- ✅ Hard for users to implement themselves

**When NOT to add a feature:**
- ❌ "Might be useful someday" (YAGNI - You Aren't Gonna Need It)
- ❌ Makes common tasks harder
- ❌ Requires major architecture changes
- ❌ Rarely used

**Extensibility Best Practices:**
1. **Use data, not code**: Store configurations, don't hardcode
2. **Plugin architecture**: New formats shouldn't require changing existing code
3. **Dependency injection**: Easy to swap implementations
4. **Interface-based design**: Code to interfaces, not implementations
5. **Sensible defaults**: Make simple things simple, complex things possible

### Tasks (Pick any that interest you)

1. **Format Capabilities System**
   - Add `capabilities` field to FormatMetadata
   - Define capability flags: `supports_images`, `supports_metadata`, `lossy_conversion`
   - Use in validation logic

2. **Conversion Validation Matrix**
   - Create `formats/conversion_matrix.py`
   - Define quality scores for conversions (fb2→mobi = excellent, pdf→mobi = poor)
   - Show warnings for lossy conversions

3. **Format Aliases**
   - Support 'jpeg' → 'jpg', 'epub3' → 'epub'
   - Add `aliases` dict to repository
   - Implement `resolve_alias()` method

4. **Format Auto-detection**
   - Read file magic bytes (not just extension)
   - Use `python-magic` library
   - Add `detect_format(file_path)` to service

5. **Configuration Presets**
   - Define common conversion presets (e.g., "kindle_optimized", "high_quality_pdf")
   - Store preset configurations
   - Allow users to select presets

### Learning Questions
- How do you design for future extensibility?
  → *Use data not code; plugin architecture; dependency injection; code to interfaces*
- What's the cost of adding features vs keeping it simple?
  → *More code to maintain/test; increased complexity; harder to understand; slower performance*
- How do you balance flexibility with complexity?
  → *YAGNI principle; sensible defaults; make simple things simple, complex things possible*

---

## 📋 Phase 8: Documentation & Cleanup

### Goal
Document the new architecture and clean up old code.

### 📚 Theory: Documentation & Code Quality

**Why Document?**
Code is read 10x more than it's written. Good documentation helps:
- **Future you**: Remember why you made decisions
- **Team members**: Understand code without reverse-engineering
- **Onboarding**: New developers get up to speed faster
- **Maintenance**: Know what's safe to change

**Simple Explanation:**
Imagine finding a recipe that just lists ingredients with no instructions. You might figure it out, but it's frustrating! Documentation is like the instructions - it explains the "how" and "why".

**Types of Documentation:**

**1. Code-level Documentation (Docstrings)**
Explains what a function/class does:
```python
def get_source_format(self, name: str) -> BaseFormat:
    """
    Retrieve a source format instance by name.
    
    Args:
        name: The format identifier (e.g., 'pdf', 'epub')
        
    Returns:
        An instance of the requested format class
        
    Raises:
        UnsupportedFormatError: If format is not registered
        
    Example:
        >>> pdf_format = service.get_source_format('pdf')
        >>> pdf_format.convert('document.pdf')
    """
```

**2. Architecture Documentation**
Explains the big picture - how components fit together:
```markdown
# Format System Architecture

## Layers
- **Domain**: Format classes, value objects (FormatMetadata)
- **Repository**: Storage and retrieval (FormatRepository)
- **Service**: Business logic (FormatService)
- **UI**: User interaction (CLI, TkUI)

## Flow
User → UI → Service → Repository → Domain Objects
```

**3. Migration Guides**
Helps developers transition to new code:
```markdown
# Migration Guide

## Old Way
```python
from formats import formats_registry
cls = formats_registry['pdf']
instance = cls()
```

## New Way
```python
from formats import format_service
instance = format_service.get_source_format('pdf')
```
```

**4. Inline Comments**
Explain WHY, not WHAT:
```python
# BAD - Obvious what it does
x = x + 1  # Increment x

# GOOD - Explains WHY
x = x + 1  # Skip header row in CSV file
```

**Code Cleanup Best Practices:**

**1. Remove Dead Code**
Commented-out code is technical debt:
```python
# BAD
# old_function()  # Removed 2024-01-15
# def old_method():
#     pass

# GOOD - Just delete it! Git history preserves it if needed
new_function()
```

**2. Remove Debug Code**
```python
# BAD
print("DEBUG: got here")
print(f"DEBUG: value = {value}")

# GOOD - Use logging if needed
import logging
logger.debug(f"Processing value: {value}")
```

**3. Consistent Naming**
```python
# BAD - Inconsistent
get_format()
retrieve_metadata()
fetch_class()

# GOOD - Consistent verbs
get_format()
get_metadata()
get_class()
```

**Type Checking with mypy:**

**What is Type Checking?**
Static analysis that verifies type hints match actual usage, catching bugs before runtime.

**Example:**
```python
def get_format(name: str) -> BaseFormat:
    return formats_registry[name]

# mypy catches this error:
result = get_format(123)  # Error: Expected str, got int

# mypy catches this error:
result = get_format('pdf')
result.nonexistent_method()  # Error: BaseFormat has no method nonexistent_method
```

**Common Type Errors:**
```python
# Missing return type
def get_format(name: str):  # mypy: Missing return type
    return formats_registry[name]

# Fix
def get_format(name: str) -> BaseFormat:
    return formats_registry[name]

# Wrong type
def process(data: dict) -> list:
    return data  # mypy: Expected list, got dict

# Fix  
def process(data: dict) -> list:
    return list(data.values())
```

**Docstring Best Practices:**

**Google Style (Recommended for this project):**
```python
def create_target_config(
    self,
    name: str,
    category: str,
    **options
) -> Target:
    """Create a configured target format object.
    
    This method validates the format exists, applies options,
    and returns a ready-to-use Target configuration.
    
    Args:
        name: Format identifier (e.g., 'pdf', 'mobi')
        category: Target category ('ebook', 'document', etc.)
        **options: Format-specific options (quality, dpi, etc.)
    
    Returns:
        Configured Target object ready for conversion
        
    Raises:
        UnsupportedFormatError: If format name is not registered
        ValueError: If options are invalid for this format
        
    Example:
        >>> target = service.create_target_config(
        ...     'pdf',
        ...     'document',
        ...     quality=95,
        ...     dpi=300
        ... )
    """
```

**Linting:**

**What is a Linter?**
A tool that analyzes code for potential errors, style violations, and code smells.

**Ruff** (used in this project) checks:
- Unused imports
- Undefined variables
- Code style (PEP 8)
- Complexity issues
- Security vulnerabilities

**Example:**
```python
# Code:
import os  # Unused import
import sys

def process():
    result = get_data()  # Undefined name
    return result

# Ruff output:
file.py:1: F401 `os` imported but unused
file.py:5: F821 undefined name `get_data`

# Fix with --fix:
uv run ruff check . --fix
```

**Documentation as Code:**

Keep docs close to code:
- ✅ Docstrings in source files
- ✅ README.md in project root
- ✅ Architecture docs in docs/ folder
- ✅ Examples in docstrings or examples/ folder

**Architecture Diagrams:**

Visual representations help understanding:
```
┌─────────────┐
│   CLI UI    │ ← User types commands
└──────┬──────┘
       │ calls
       ▼
┌─────────────┐
│FormatService│ ← Validates, orchestrates
└──────┬──────┘
       │ uses
       ▼
┌─────────────┐
│ Repository  │ ← Stores/retrieves formats
└──────┬──────┘
       │ returns
       ▼
┌─────────────┐
│Format Class │ ← Does actual conversion
└─────────────┘
```

### Tasks
1. **Create Documentation**
   - Update `FACTORY_PATTERN_SUMMARY.md` with new architecture
   - Add architecture diagrams showing Repository + Service layers
   - Create migration guide for developers
   - Add docstrings to all new classes/methods

2. **Remove Deprecated Code**
   - Remove debug print statements
   - Remove unused `my_reg` and `resg` decorator
   - Clean up comments
   - Run linter: `uv run ruff check . --fix`

3. **Type Checking**
   - Run `uv run mypy .`
   - Fix any type errors
   - Add missing type hints

4. **Update AGENTS.md**
   - Document the new patterns used
   - Add examples of using format_service

---

## 🎓 Learning Resources

### Concepts to Study
1. **Domain-Driven Design (DDD)**
   - Value Objects vs Entities
   - Repository Pattern
   - Service Layer
   - Ubiquitous Language

2. **Design Patterns**
   - Repository Pattern
   - Service Layer Pattern
   - Factory Pattern
   - Dependency Injection

3. **SOLID Principles**
   - Review how each principle applies to this refactoring

4. **Clean Architecture**
   - Layers: Domain → Repository → Service → UI
   - Dependency rules (dependencies point inward)

### Recommended Reading
- "Domain-Driven Design" by Eric Evans (chapters on Value Objects, Repositories, Services)
- "Clean Architecture" by Robert C. Martin
- "Patterns of Enterprise Application Architecture" by Martin Fowler

---

## ✅ Success Criteria

You'll know you succeeded when:

1. ✅ **Separation of Concerns**: Format storage, business logic, and UI are clearly separated
2. ✅ **Clear API**: No confusion about classes vs instances
3. ✅ **Testability**: Can test each layer independently with mocks
4. ✅ **Type Safety**: No type errors when running mypy
5. ✅ **User Experience**: Better error messages and format selection
6. ✅ **Extensibility**: Easy to add new formats or features
7. ✅ **Understanding**: You can explain WHY each pattern was chosen

---

## 💡 Tips for Learning

1. **Implement incrementally** - Don't try to do everything at once
2. **Write tests first** - TDD helps you understand what you're building
3. **Draw diagrams** - Visualize the relationships between classes
4. **Ask "why"** - For every design decision, understand the reasoning
5. **Refactor gradually** - Keep the old code working while building new
6. **Read existing code** - Look at your processors/savers for similar patterns
7. **Experiment** - Try different approaches, see what feels right

Good luck! This is a real-world refactoring that teaches professional software architecture patterns. Take your time and enjoy the learning process! 🚀
