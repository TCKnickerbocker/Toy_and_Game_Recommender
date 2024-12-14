# Use the official Grafana base image
FROM grafana/grafana-oss:latest

# Set working directory
WORKDIR /usr/share/grafana

# Copy custom configuration files (if any)
# Uncomment and adjust the line below to copy a custom Grafana configuration file
COPY grafana.ini /etc/grafana/grafana.ini

# Copy custom dashboards and plugins (if needed)
COPY dashboards /var/lib/grafana/dashboards
COPY plugins /var/lib/grafana/plugins

# Expose default Grafana port
EXPOSE 3000

# Set environment variables (optional, can also be set in docker-compose or runtime)
ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=admin

# Start the Grafana server
CMD ["/run.sh"]

