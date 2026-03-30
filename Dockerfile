FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + gosu for entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl gosu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir streamlit-shadcn-ui streamlit-mermaid requests

# Copy project
COPY . .

# Create data directories and ensure they exist
RUN mkdir -p /app/data/db /app/data/real /app/data/sample

# Generate sample data (as root, before switching user)
RUN python data/generators/synthetic_data.py

# Verify modules load
RUN python -c "import sys; sys.path.insert(0,'.'); from agents.config import AGENT_CONFIG; print(f'Agents OK: {len(AGENT_CONFIG)} config keys')"
RUN python -c "import sys; sys.path.insert(0,'.'); from utils.template_generator import generate_template; t=generate_template(); print(f'Template OK: {len(t):,} bytes')"
RUN python -c "from apscheduler.schedulers.blocking import BlockingScheduler; print('Scheduler OK')"

# Set ownership for all data dirs
RUN chown -R appuser:appuser /app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8510

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8510/_stcore/health || exit 1

# Entrypoint fixes volume permissions at runtime, then runs CMD
ENTRYPOINT ["/app/entrypoint.sh"]

# Run Streamlit
CMD ["streamlit", "run", "app.py", \
     "--server.port=8510", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.fileWatcherType=none"]
