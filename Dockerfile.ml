FROM gcr.io/pdzr-458820/padelyzer-api-base

# Copy ML installation script
COPY install_ml_deps.sh .

# Install ML dependencies
RUN ./install_ml_deps.sh 