FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy analyst agent source
COPY src/ ./src/

# Ensure the app src directory is in the PYTHONPATH
ENV PYTHONPATH=/app/src

EXPOSE 8001

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001"]
