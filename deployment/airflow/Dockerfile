# Use the latest Apache Airflow image with Python 3.10
FROM apache/airflow:2.6.0-python3.10

# Set the working directory
WORKDIR /opt/airflow

# Install additional dependencies if needed
# RUN pip install --no-cache-dir <additional-packages>

# Set the entrypoint for the container
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["webserver"]