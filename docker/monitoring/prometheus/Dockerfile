FROM prom/prometheus:v3.0.1

# Copy configuration with explicit permissions
COPY --chmod=644 docker/monitoring/prometheus/prometheus.yml /etc/prometheus/prometheus.yml

# Use default entrypoint and cmd from base image
# Expose Prometheus ports
EXPOSE 9100 9101 9102

