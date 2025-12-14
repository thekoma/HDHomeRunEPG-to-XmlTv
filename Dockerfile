FROM python:3.9-slim

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
USER appuser

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
