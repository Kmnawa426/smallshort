# Use official Playwright image with all browsers & dependencies
FROM mcr.microsoft.com/playwright:focal

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip using python3 -m pip
RUN python3 -m pip install --upgrade pip

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt

# Run the bot
CMD ["python3", "bot.py"]
