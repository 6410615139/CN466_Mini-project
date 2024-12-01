FROM python:3.11

# Create app directory
WORKDIR /usr/src/app

# Install app dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bundle app source
COPY . .

EXPOSE 80
# CMD ["python", "-u", "app.py"]
CMD ["sh", "start.sh"]