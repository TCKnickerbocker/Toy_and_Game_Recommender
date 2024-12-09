# FROM prom/prometheus:v2.51.0

# # Copy configuration file first
# COPY docker/monitoring/prometheus/prometheus.yml /etc/prometheus/prometheus.yml

# # Use root temporarily to set permissions
# USER root

# # Set correct permissions without using chown
# RUN chmod 644 /etc/prometheus/prometheus.yml

# # Create data directory with correct permissions
# RUN mkdir -p /prometheus/data && \
#     chmod 755 /prometheus/data

# # Switch back to prometheus user (built-in to official image)
# USER nobody

# EXPOSE 9090 9091

# WORKDIR /prometheus

# # Default CMD will be used from base image


FROM prom/prometheus:v3.0.1

# Copy configuration with explicit permissions
COPY --chmod=644 docker/monitoring/prometheus/prometheus.yml /etc/prometheus/prometheus.yml

# Use default entrypoint and cmd from base image
# Expose Prometheus ports
EXPOSE 9100 9101 9102

