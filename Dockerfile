FROM --platform=linux/amd64 python:3.10-alpine 

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add chromium chromium-chromedriver

# upgrade pip
RUN pip install --upgrade pip

# Setup Environment
WORKDIR /app
RUN mkdir results
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "parse.py"]