## Overview
The Equipment Maintenance System is a web-based application built for Ryanair to manage and track the maintenance lifecycle of ground and operational equipment. It provides a centralised platform for logging equipment records, scheduling service intervals, recording maintenance activity, and monitoring the overall health of assets across locations. The system is built using Flask, served by Gunicorn, and deployed to AWS Elastic Beanstalk.

## Technology Stack

The backend is written in Python using the Flask web framework. The application uses SQLite as its embedded database, managed entirely through Python's built-in sqlite3 module with no external ORM dependency. Gunicorn acts as the WSGI server and sits behind an Nginx reverse proxy on the AWS instance. The frontend is served as a static HTML template rendered by Flask's Jinja2 templating engine. The application is deployed on AWS Elastic Beanstalk in the us-west-2 region.
## API Endpoints

The application exposes a RESTful JSON API. The /api/health endpoint returns the running status of the system. The /api/dashboard endpoint returns a summary of total equipment count, items due for service within 14 days, equipment currently in service, and the total number of maintenance records. The /api/equipment endpoint supports GET requests with optional filters for search term, status, and equipment type, as well as POST requests to create new equipment entries. Individual equipment records can be updated or deleted via PUT and DELETE requests to /api/equipment/<id>. Maintenance records are managed through /api/maintenance, which supports GET and POST, and individual records can be deleted via /api/maintenance/<id>.

 ## Deployment
 The application is deployed to AWS Elastic Beanstalk using the EB CLI. To deploy a new version, activate the virtual environment and run "eb deploy" from the project root. Elastic Beanstalk automatically installs dependencies from requirements.txt, starts Gunicorn using the Procfile, and routes traffic through Nginx. Logs can be retrieved at any time using "eb logs" and the application URL can be opened with "eb open".

 Deployment link : http://equipmentmaintencesystemforryanair-dev.us-west-2.elasticbeanstalk.com/

## Run Locally
1. clone repository to your local machine.
   'git clone <https://github.com/sampathreddy29/programming-for-assignment> 

2. Create a virtual environment:
   `python -m venv .venv`
3. Activate it:
   `.\.venv\Scripts\Activate.ps1`
4. Install dependencies:
   `pip install -r requirements.txt`
5. Start the server:
   `python app.py`
6. Open:
   `http://127.0.0.1:5000`

