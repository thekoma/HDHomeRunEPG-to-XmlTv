import sys
import os
import subprocess


def main():
    # Assume venv is in project root. Script is in scripts/ folder.
    # project_root is one level up from the directory containing this script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    if sys.platform == "win32":
        # Windows path: venv/Scripts/pytest.exe
        pytest_executable = os.path.join(project_root, "venv", "Scripts", "pytest.exe")
    else:
        # Linux/Unix path: venv/bin/pytest
        pytest_executable = os.path.join(project_root, "venv", "bin", "pytest")

    if not os.path.exists(pytest_executable):
        # Fallback check for .venv if venv not found (just in case)
        if sys.platform == "win32":
            alt_executable = os.path.join(
                project_root, ".venv", "Scripts", "pytest.exe"
            )
        else:
            alt_executable = os.path.join(project_root, ".venv", "bin", "pytest")

        if os.path.exists(alt_executable):
            pytest_executable = alt_executable
        else:
            print(f"Error: pytest executable not found at {pytest_executable}")
            print(
                "Please ensure virtual environment is created in 'venv' (or '.venv') and dependencies are installed."
            )
            sys.exit(1)

    # Pass all arguments received by this script to pytest
    cmd = [pytest_executable] + sys.argv[1:]

    # Run
    try:
        # Use shell=False is safer and usually fine here.
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Failed to run pytest: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
