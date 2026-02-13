FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Download ML models from HuggingFace (not in Git, gitignored)
# Models are stored on HuggingFace Spaces and downloaded at build time
RUN python -c "\
from huggingface_hub import hf_hub_download; \
import shutil, os; \
os.makedirs('src/models', exist_ok=True); \
[shutil.copy( \
    hf_hub_download('ClementRbl/deploy-ml', f'src/models/{m}', repo_type='space'), \
    f'src/models/{m}' \
) for m in ['energy_model.joblib', 'co2_model.joblib']]; \
print('Models downloaded successfully'); \
[print(f'  {m}: {os.path.getsize(f\"src/models/{m}\")} bytes') for m in ['energy_model.joblib', 'co2_model.joblib']]; \
"

# Create non-root user for security
RUN useradd -m -u 1000 appuser
USER appuser

# Expose port
EXPOSE 7860

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV API_HOST=0.0.0.0
ENV API_PORT=7860

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
