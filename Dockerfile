FROM python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN addgroup --gid 1001 appuser && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser

# Copy the library and application
COPY --chown=appuser:appuser hdhomerun_epg/ /code/hdhomerun_epg/
COPY --chown=appuser:appuser app/ /code/app/

# Expose port
EXPOSE 8000

# Switch to non-root user
USER 1001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
