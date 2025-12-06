# Drive Synapsis - Google Drive MCP Server
# https://github.com/your-repo/drive-synapsis

FROM python:3.11-slim

LABEL maintainer="Drive Synapsis"
LABEL description="Google Drive MCP Server for AI Assistants"

# Set working directory
WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -e .

# Create directory for credentials (to be mounted)
RUN mkdir -p /app/credentials

# Set environment variable for credentials location
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/client_secret.json

# The MCP server communicates via stdio
# This is typically run as a subprocess by the AI client
CMD ["drive-synapsis"]
