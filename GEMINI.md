# HDHomeRunEPG to XMLTV Refactoring Project

## Goal
Transform the existing single-script Python application into a modular, importable library and a containerized FastAPI service. The service will fetch EPG data from HDHomeRun devices and serve it as XMLTV format.

## Process
1.  **Refactoring**: Break down `HDHomeRunEPG_To_XmlTv.py` into a Python package structure.
2.  **Library Creation**: Ensure core logic (device discovery, fetching data, XML generation) is reusable and decoupled from CLI arguments.
3.  **FastAPI Implementation**: Create a web service exposing an endpoint (e.g., `/epg.xml`) to retrieve the generated XML for an HDHomeRun Device.
4.  **Configuration**: Switch/Augment configuration to support Environment Variables for container usage.
5.  **Containerization**: Update/Refine Docker setup to run the FastAPI service.

## Output
-   A Python package (e.g., `hdhomerun_epg`).
-   A FastAPI application entry point.
-   A Docker image definition capable of running the service.

## Rules
-   **Portability**: Code must be runnable as a library or a service.
-   **Configuration**: All parameters (Host, Days, Hours, etc.) must be configurable via Environment Variables (priority) or CLI/Defaults.
-   **Clean Code**:
    -   Use Type Hinting (e.g., `def foo(d: int) -> str:`).
    -   Avoid functional globals; pass dependencies or use class instances.
    -   Proper logging setup using specific loggers, not just root.
-   **Step-by-Step**: Execute changes in granular steps with verification/commit-points (simulated via file updates).