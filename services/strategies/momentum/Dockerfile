FROM python:3.12-slim

# Install base system deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Setup app
WORKDIR /app
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]