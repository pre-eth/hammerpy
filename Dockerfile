FROM python:3.12.1-slim

# Download Package Information
# Install chrome, chromedriver, and tk
RUN apt-get update -y; \
    apt-get install -y unzip wget curl tk; \
    # install google chrome
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb; \
    apt-get install -y ./google-chrome-stable_current_amd64.deb; \
    # install chromedriver
    wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip; \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin

ADD hammer.py requirements.txt ./
ADD hammerpy ./hammerpy
ADD img ./img

RUN pip install -r requirements.txt

CMD [ "python3", "hammer.py" ]