# E-book Converter - Documentation Index

This document serves as the main entry point for all project documentation, providing links and summaries of the comprehensive analysis and architectural documentation.

## Documentation Files

### 📊 [PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md)
**Comprehensive Project Analysis**
- Complete codebase structure analysis
- Class-by-class breakdown with file references
- Design patterns implementation details
- Architecture quality assessment
- Code examples and usage patterns

### 🏗️ [CLASS_DIAGRAM.md](./CLASS_DIAGRAM.md)
**UML Class Diagrams**
- Detailed class relationship diagrams using Mermaid
- Interface implementations and inheritance hierarchies
- Component interaction sequence diagrams
- Design pattern visualization
- Exception hierarchy mapping

### 🎯 [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md)
**Architectural Views**
- System architecture overview
- Component interaction flows
- Data flow diagrams
- Package dependency graphs
- Deployment architecture
- Threading and concurrency models

## Quick Reference

### Core Architecture
```
┌─────────────────────┐
│   User Interfaces   │ ← CLI, Tkinter GUI, Web
├─────────────────────┤
│   Converter Engine  │ ← Main orchestrator
├─────────────────────┤
│   Processors        │ ← Local, Docker, Remote
├─────────────────────┤
│   Savers            │ ← Local FS, Google Drive
├─────────────────────┤
│   Workers           │ ← Threading, Concurrency
└─────────────────────┘
```

### Key Design Patterns
- **Strategy Pattern**: Pluggable processors, UIs, savers
- **Dependency Injection**: Interface-based design
- **Observer Pattern**: Event handling and notifications
- **Factory Pattern**: Format registry system
- **Template Method**: Conversion workflow
- **Command Pattern**: Job processing abstraction

### Main Classes and Their Responsibilities

| Class | File | Responsibility |
|-------|------|----------------|
| `Converter` | `converter.py:27` | Main orchestrator, coordinates all operations |
| `JobConfig` | `config.py:66` | Configuration management with validation |
| `LocalProcessor` | `processors/local_processor.py:11` | Local ebook-convert execution |
| `ProcessorOnDocker` | `processors/processor_on_docker.py:157` | Docker-based processing |
| `JobProcessorRemote` | `processors/remote_processor.py:19` | Remote API communication |
| `LocalFileSaver` | `savers/local_saver.py:14` | Local filesystem operations |
| `GoogleDriveSaver` | `savers/google_drive_saver.py:62` | Google Drive integration |
| `ConverterInterfaceCLI` | `uis/cli_ui.py:25` | Command-line interface |
| `ConverterInterfaceTk` | `uis/tk_ui.py:31` | Tkinter GUI interface |
| `ThreadWorker` | `workers/worker.py:86` | Concurrent execution |

### Interface Contracts

#### JobProcessor Interface
```python
def send_job(filename: str, options: dict | None = None) -> int
def get_job_status(job_id: int) -> Generator
def get_job_result(job_id: int) -> str
def save_file(path_to_result: str, path_to_save: str | Path) -> str | Path | PosixPath
```

#### SaverProtocol Interface
```python
def setup(**kwargs: Any) -> None
def save(source_path: str | None = None) -> str | Path | PosixPath
```

#### UIProtocol Interface
```python
def run(converter: Converter) -> None
def setup() -> Config | bool
def convert(config: Config) -> None
def display_job_status(status: str) -> None
def display_job_result(result: Union[Path, str]) -> None
def display_error(error: str, status: ConverterStatus) -> None
```

### Extension Points

The architecture is designed for easy extension:

1. **New Processors**: Implement `JobProcessor` interface
2. **New UIs**: Implement `UIProtocol`
3. **New Savers**: Implement `SaverProtocol`
4. **New Workers**: Implement `Worker` protocol
5. **New Formats**: Use `@register_format` decorator

### Usage Examples

#### CLI Usage
```bash
# Basic conversion
uv run main.py --ui cli -path book.fb2 -t mobi

# With custom category
uv run main.py --ui cli -path book.fb2 -t mobi -cat ebook
```

#### GUI Usage
```bash
# Launch Tkinter GUI
uv run main.py --ui tk

# Default (GUI)
uv run main.py
```

#### Programmatic Usage
```python
from converter import Converter
from processors.local_processor import LocalProcessor
from savers.local_saver import LocalFileSaver
from uis.cli_ui import ConverterInterfaceCLI
from workers.worker import ThreadWorker
from config import JobConfig, Target

# Setup components
interface = ConverterInterfaceCLI()
processor = LocalProcessor()
saver = LocalFileSaver()
worker = ThreadWorker()

# Create converter
converter = Converter(interface, processor, saver, worker)

# Configure job
target = Target("mobi", "ebook")
config = JobConfig(target, "path/to/book.fb2", "output/")

# Execute conversion
converter.convert(config)
```

### Development Commands

#### Testing
```bash
# Run all tests
uv run pytest

# Run specific test
uv run pytest tests/test_converter.py::ConverterTestCase::test_main_convert
```

#### Code Quality
```bash
# Type checking
uv run mypy .

# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Fix linting issues
/fix-lint
```

#### Running the Application
```bash
# CLI interface
uv run main.py --ui cli

# GUI interface
uv run main.py --ui tk

# Web service (Docker)
cd service_project
docker-compose up --build
```

### Service Project (Web Interface)

The project includes a complete web service implementation:

- **Backend**: FastAPI/Flask service (`service_project/backend/`)
- **Frontend**: React application (`service_project/frontend/`)
- **Deployment**: Docker Compose setup
- **Ports**: Frontend (5173), Backend (8000)

### Error Handling

The project implements comprehensive error handling:

- **ConvertError**: Conversion-specific issues
- **ProcessorError**: Processing failures
- **InterfaceError**: UI-related problems
- **ParamsError**: Configuration validation errors

### Dependencies

#### Core Dependencies
- `docker`: Container management
- `requests`: HTTP communication
- `ttkbootstrap`: Modern Tkinter styling
- `google-api-python-client`: Google Drive integration
- `tkthread`: Thread-safe Tkinter operations

#### Development Dependencies
- `pytest`: Testing framework
- `mypy`: Type checking
- `ruff`: Linting and formatting
- `uv`: Package management

### File Structure Summary

```
convert/
├── 📄 PROJECT_ANALYSIS.md        # This comprehensive analysis
├── 📄 CLASS_DIAGRAM.md           # UML class diagrams
├── 📄 ARCHITECTURE_DIAGRAMS.md   # Architecture visualizations
├── 📄 DOCUMENTATION_INDEX.md     # This index file
├── 📄 README.md                  # Getting started guide
├── 🎯 main.py                    # Application entry point
├── ⚙️ converter.py               # Core business logic
├── ⚙️ config.py                  # Configuration classes
├── 🛠️ utils.py                   # Utility functions
├── 📁 interfaces/                # Protocol definitions
├── 📁 processors/                # Processing implementations
├── 📁 savers/                    # Saving implementations
├── 📁 uis/                       # User interface implementations
├── 📁 workers/                   # Concurrency implementations
├── 📁 formats/                   # Format system
├── 📁 tests/                     # Test suite
└── 📁 service_project/           # Web service
```

## Architecture Quality Assessment

### Strengths
✅ **High Cohesion**: Each class has a single, well-defined responsibility  
✅ **Loose Coupling**: Components interact through interfaces  
✅ **Extensibility**: Easy to add new implementations without modifying existing code  
✅ **Testability**: Dependency injection enables comprehensive unit testing  
✅ **SOLID Principles**: All five SOLID principles are well-implemented  
✅ **Design Patterns**: Appropriate use of established patterns  
✅ **Error Handling**: Comprehensive exception hierarchy  
✅ **Documentation**: Well-documented interfaces and classes  

### Areas for Improvement
🔄 **Type Safety**: Some type annotation inconsistencies (noted in diagnostics)  
🔄 **Error Messages**: Could be more specific in some cases  
🔄 **Configuration Validation**: More robust validation could be added  
🔄 **Logging**: More comprehensive logging throughout the application  

This documentation provides a complete view of the e-book converter architecture, making it easy for developers to understand, maintain, and extend the system.
