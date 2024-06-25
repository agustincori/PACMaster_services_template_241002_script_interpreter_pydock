# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP=db_manager.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD flask run --host=0.0.0.0 --port=$PORT