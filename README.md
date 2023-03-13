# EBA-Analyzer

This application is written in Python and is used to download the latest EBA registry and parse data from it.

Due to the fact that the EBA registry site uses a button that uses JS to generate a link, it cannot be retrieved by scrapping the site using something like `requests` or `beautifulsoup`. Therefore `selenium` is used which controls a Chromium browser and can mimic real user interaction. To simplify the launch process `Docker` and `Docker Compose` are used to automate the deployment.
## Requirements
Before starting the application, make sure you have Docker and Docker Compose installed.

## Launching Application
Go to the project root directory and enter the following command:
```bash
docker compose up --build
```

After the container exits, you will see a directory called `results` in which you can find a file called `results.json`

## File structure
The main files are as follows:
* `parse.py` - Contains the python script that performs the parsing. 
* `countries.csv` - Stores countries and their abbreviations. This document is taken from the EBA API specification
* `requirements.txt` - Stores requirements for the script that needs to be installed.
* `Dockerfile` - stores instructions for Docker image creation
* `docker-compose.yml` - stores instruction for creating container and sharing required volumes