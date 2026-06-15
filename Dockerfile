FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces requires a non-root user (id 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

COPY --chown=user requirements.txt .

# Install dependencies
RUN pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY --chown=user . .

# Ensure the app can write to models and database
RUN mkdir -p /home/user/app/models

EXPOSE 7860

# Start FastAPI using uvicorn
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "7860"]
