# E-book Converter - Architecture Diagrams

This document contains various architectural diagrams that illustrate the structure and relationships within the E-book Converter project.

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI[Command Line Interface]
        GUI[Tkinter GUI]
        WEB[Web Interface]
    end
    
    subgraph "Core Logic"
        CONV[Converter Engine]
        CONFIG[Configuration Manager]
    end
    
    subgraph "Processing Layer"
        LOCAL[Local Processor]
        DOCKER[Docker Processor]
        REMOTE[Remote API Processor]
    end
    
    subgraph "Storage Layer"
        LSAVE[Local File Saver]
        GSAVE[Google Drive Saver]
    end
    
    subgraph "Concurrency"
        WORKER[Thread Worker]
        SIGNAL[Observer/Signal]
    end
    
    subgraph "Format System"
        REGISTRY[Format Registry]
        FB2[FB2 Format]
        MOBI[MOBI Format]
    end
    
    CLI --> CONV
    GUI --> CONV
    WEB --> CONV
    
    CONV --> CONFIG
    CONV --> LOCAL
    CONV --> DOCKER
    CONV --> REMOTE
    CONV --> LSAVE
    CONV --> GSAVE
    CONV --> WORKER
    
    WORKER --> SIGNAL
    CONV --> REGISTRY
    REGISTRY --> FB2
    REGISTRY --> MOBI
```

## Component Interaction Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as User Interface
    participant Conv as Converter
    participant Proc as Processor
    participant Saver as Saver
    participant Worker as Worker

    User->>UI: Select file & format
    UI->>Conv: setup() -> JobConfig
    UI->>Conv: convert(config)
    
    Conv->>Worker: execute(_convert)
    Worker->>Conv: _convert()
    
    Conv->>Conv: validate_config()
    Conv->>Conv: validate_path()
    
    Conv->>Proc: send_job(file, options)
    Proc-->>Conv: job_id
    
    Conv->>UI: display_common_info(job_id)
    
    loop Processing Status
        Conv->>Proc: get_job_status(job_id)
        Proc-->>Conv: status_message
        Conv->>UI: display_common_info(status)
    end
    
    Conv->>Proc: get_job_result(job_id)
    Proc-->>Conv: result_path
    
    Conv->>Saver: setup(source_path, destination_path)
    Conv->>Saver: save()
    Saver-->>Conv: saved_path
    
    Conv->>UI: display_job_result(saved_path)
    UI->>User: Show completion
```

## Class Hierarchy Diagram

```mermaid
classDiagram
    %% Abstract Base Classes
    class JobProcessor {
        <<abstract>>
        +send_job()
        +get_job_status()
        +get_job_result()
        +save_file()
    }
    
    class SaverProtocol {
        <<abstract>>
        +setup()
        +save()
    }
    
    class UIProtocol {
        <<protocol>>
        +run()
        +setup()
        +convert()
        +display_*()
    }
    
    class Worker {
        <<protocol>>
        +execute()
        +is_completed()
        +get_result()
    }
    
    class Format {
        <<abstract>>
        +allowed_formats()
        +get_options()
        +get_extension()
    }
    
    %% Concrete Implementations
    LocalProcessor --|> JobProcessor
    ProcessorOnDocker --|> LocalProcessor
    JobProcessorRemote --|> JobProcessor
    
    LocalFileSaver --|> SaverProtocol
    GoogleDriveSaver --|> SaverProtocol
    
    ConverterInterfaceCLI --|> UIProtocol
    ConverterInterfaceTk --|> UIProtocol
    
    ThreadWorker --|> Worker
    
    Fb2Format --|> Format
    MobiFormat --|> Format
    
    %% Core Classes
    class Converter {
        -interface: UIProtocol
        -processor: JobProcessor
        -saver: SaverProtocol
        -worker: Worker
        +convert()
        +send_job()
        +get_result()
        +save()
    }
    
    Converter --> UIProtocol
    Converter --> JobProcessor
    Converter --> SaverProtocol
    Converter --> Worker
```

## Data Flow Diagram

```mermaid
flowchart TD
    A[User Input] --> B[UI Interface]
    B --> C[Job Configuration]
    C --> D[Converter Engine]
    
    D --> E{Validation}
    E -->|Valid| F[Send to Processor]
    E -->|Invalid| G[Error Display]
    
    F --> H{Processor Type}
    H -->|Local| I[Local ebook-convert]
    H -->|Docker| J[Docker Container]
    H -->|Remote| K[Remote API]
    
    I --> L[Processing Status]
    J --> L
    K --> L
    
    L --> M[Monitor Progress]
    M --> N{Complete?}
    N -->|No| M
    N -->|Yes| O[Get Result]
    
    O --> P[Saver Component]
    P --> Q{Save Location}
    Q -->|Local| R[Local Filesystem]
    Q -->|Cloud| S[Google Drive]
    
    R --> T[Final Result]
    S --> T
    T --> U[Display to User]
    
    G --> U
```

## Package Dependencies

```mermaid
graph LR
    subgraph "External Dependencies"
        DOCKER[docker]
        REQUESTS[requests]
        TKINTER[tkinter/ttkbootstrap]
        GOOGLE[google-api-python-client]
        PYTEST[pytest]
    end
    
    subgraph "Core Modules"
        MAIN[main.py]
        CONV[converter.py]
        CONFIG[config.py]
        UTILS[utils.py]
    end
    
    subgraph "Interface Layer"
        IPROC[processor_interface]
        ISAVER[saver_interface]
        IUI[ui_interface]
        IWORK[worker_interface]
    end
    
    subgraph "Implementation Layer"
        PROC[processors/]
        SAVE[savers/]
        UI[uis/]
        WORK[workers/]
        FMT[formats/]
    end
    
    MAIN --> CONV
    MAIN --> CONFIG
    MAIN --> PROC
    MAIN --> SAVE
    MAIN --> UI
    MAIN --> WORK
    
    CONV --> IPROC
    CONV --> ISAVER
    CONV --> IUI
    CONV --> IWORK
    CONV --> CONFIG
    
    PROC --> IPROC
    PROC --> DOCKER
    PROC --> REQUESTS
    
    SAVE --> ISAVER
    SAVE --> GOOGLE
    
    UI --> IUI
    UI --> TKINTER
    
    WORK --> IWORK
    
    FMT --> UTILS
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV[Local Development]
        TEST[Unit Tests]
        LINT[Linting/Type Check]
    end
    
    subgraph "Desktop Application"
        CLI_APP[CLI Application]
        GUI_APP[Tkinter GUI]
        LOCAL_PROC[Local Processing]
        DOCKER_PROC[Docker Processing]
    end
    
    subgraph "Web Application"
        FRONTEND[React Frontend]
        BACKEND[FastAPI Backend]
        WEB_API[Web API]
    end
    
    subgraph "External Services"
        REMOTE_API[Remote Conversion API]
        GDRIVE_API[Google Drive API]
        DOCKER_HUB[Docker Registry]
    end
    
    subgraph "Storage"
        LOCAL_FS[Local Filesystem]
        CLOUD_STORAGE[Cloud Storage]
    end
    
    DEV --> CLI_APP
    DEV --> GUI_APP
    DEV --> FRONTEND
    
    CLI_APP --> LOCAL_PROC
    CLI_APP --> DOCKER_PROC
    GUI_APP --> LOCAL_PROC
    GUI_APP --> DOCKER_PROC
    
    FRONTEND --> BACKEND
    BACKEND --> WEB_API
    
    LOCAL_PROC --> LOCAL_FS
    DOCKER_PROC --> DOCKER_HUB
    WEB_API --> REMOTE_API
    
    CLI_APP --> GDRIVE_API
    GUI_APP --> GDRIVE_API
    WEB_API --> CLOUD_STORAGE
```

## Error Handling Flow

```mermaid
flowchart TD
    A[Operation Start] --> B{Try Operation}
    B -->|Success| C[Continue Flow]
    B -->|Exception| D[Catch Exception]
    
    D --> E{Exception Type}
    E -->|ConvertError| F[Conversion Issues]
    E -->|ProcessorError| G[Processing Issues]
    E -->|InterfaceError| H[UI Issues]
    E -->|ParamsError| I[Configuration Issues]
    E -->|Other| J[General Error]
    
    F --> K[Set Status: FAILED]
    G --> K
    H --> K
    I --> K
    J --> K
    
    K --> L[Log Error]
    L --> M[Display Error to User]
    M --> N[Cleanup Resources]
    N --> O[End]
    
    C --> P[Success Path]
    P --> Q[Set Status: COMPLETED]
    Q --> R[Display Result]
    R --> S[End]
```

## Threading Model

```mermaid
graph TB
    subgraph "Main Thread"
        UI_MAIN[UI Main Loop]
        CONV_MAIN[Converter Main]
    end
    
    subgraph "Worker Thread"
        WORKER[Thread Worker]
        PROC_EXEC[Processing Execution]
    end
    
    subgraph "Background Threads"
        STATUS[Status Monitoring]
        DOCKER_BUILD[Docker Build]
    end
    
    subgraph "Synchronization"
        SIGNAL[Signal/Observer]
        QUEUE[Thread Queue]
    end
    
    UI_MAIN --> CONV_MAIN
    CONV_MAIN --> WORKER
    WORKER --> PROC_EXEC
    
    PROC_EXEC --> STATUS
    DOCKER_BUILD --> SIGNAL
    
    WORKER --> SIGNAL
    STATUS --> QUEUE
    SIGNAL --> UI_MAIN
```

## Design Patterns Map

```mermaid
mindmap
  root((Design Patterns))
    Strategy
      Processor Types
      UI Types
      Saver Types
    
    Dependency Injection
      Converter Constructor
      Interface Dependencies
    
    Observer
      Signal Class
      Error Handling
      Status Updates
    
    Factory
      Format Registry
      Dynamic Loading
    
    Template Method
      Converter Workflow
      Processing Steps
    
    Command
      Job Processing
      Operation Encapsulation
    
    Facade
      Converter Interface
      Simplified API
    
    Registry
      Format Management
      Plugin System
```

These diagrams provide multiple perspectives on the architecture:

1. **System Architecture** - High-level component overview
2. **Component Interaction** - How components communicate
3. **Class Hierarchy** - Inheritance and implementation relationships
4. **Data Flow** - How data moves through the system
5. **Package Dependencies** - Module dependencies and external libraries
6. **Deployment Architecture** - Different deployment scenarios
7. **Error Handling** - Error propagation and handling
8. **Threading Model** - Concurrency and synchronization
9. **Design Patterns** - Applied patterns and their purposes

Each diagram focuses on a specific aspect of the system to provide clear understanding of the architecture from different viewpoints.