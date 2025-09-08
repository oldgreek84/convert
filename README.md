# E-book Converter

A versatile e-book conversion tool that supports various processing methods and user interfaces. This project is designed with a modular architecture, allowing for flexible integration of different conversion processors (local, Dockerized, remote) and user interfaces (CLI, Tkinter, Web).

## Features

*   **Multiple Processors**: Choose between local, Docker-based, or remote processing for e-book conversions.
*   **Flexible User Interfaces**: Interact with the converter via a Command-Line Interface (CLI), a Tkinter-based GUI, or a web application.
*   **Modular Design**: Easily extend with new processors or UIs.
*   **Docker Support**: Run the web service (backend and frontend) using Docker Compose for easy deployment.

## Project Structure

*   `converter.py`: Core logic for e-book conversion.
*   `config.py`: Application configuration settings.
*   `interfaces/`: Defines abstract base classes for processors, UIs, and workers.
*   `processors/`:
    *   `local_processor.py`: Processor for local execution.
    *   `processor_on_docker.py`: Processor that utilizes a Docker container for conversion.
    *   `remote_processor.py`: Processor for remote conversion services.
*   `uis/`:
    *   `cli_ui.py`: Command-Line Interface for the converter.
    *   `tk_ui.py`: Tkinter-based Graphical User Interface.
*   `workers/`: Contains background worker implementations.
*   `service_project/`: A web-based interface for the converter.
    *   `backend/`: Python backend (FastAPI/Flask) for the web service.
    *   `frontend/`: React-based frontend for the web service.
    *   `docker-compose.yml`: Docker Compose configuration to run the web service.
*   `tests/`: Unit and integration tests for the project.
*   `main.py`: The main entry point for running the application (CLI/Tkinter).

## Getting Started

### Prerequisites

*   Python 3.x
*   pip (Python package installer)
*   Docker (for Docker-based processors or the web service)
*   Node.js and npm (for developing the web frontend)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/e-book-converter.git
    cd e-book-converter
    ```

2.  **Set up Python environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

### Running the Application

#### 1. Command-Line Interface (CLI)

To run the CLI version of the converter:

```bash
python main.py --ui cli
```

#### 2. Tkinter GUI

To run the Tkinter-based GUI:

```bash
python main.py --ui tk
```

#### 3. Web Service (using Docker Compose)

To run the web-based converter using Docker Compose (includes both backend and frontend):

1.  **Build and start the services:**
    ```bash
    docker-compose -f service_project/docker-compose.yml up --build
    ```
2.  **Access the application:**
    *   Frontend: `http://localhost:5173` (or the port specified in `service_project/frontend/vite.config.js`)
    *   Backend API: `http://localhost:8000` (or the port specified in `service_project/backend/app/main.py`)

### Running Tests

To run the unit and integration tests:

```bash
pytest
```

## Configuration

Configuration settings can be found in `config.py`. You can modify this file to change default processors, UI settings, or other application parameters.

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` (if it exists, otherwise, this is a placeholder) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
