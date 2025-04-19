# Use the latest Python image with a specific version
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clone the scrape sentiment project from the release branch
RUN git clone --branch release https://github.com/your-username/scrape-sentiment.git /app/scrape_sentiments

# Set the working directory to the cloned project
WORKDIR /app/scrape_sentiments

# Set the entry point for the container
CMD ["python", "main.py"]