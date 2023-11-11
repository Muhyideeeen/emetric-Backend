# e-metric-api-revamp

### Project Setup

* Clone the repository
* Set up your postgres database
* Install python and have virtual env activated
* Install redis and have redis started and running
* Copy your .env.example and make a .env file in same folder and populate the env
* Install libraries with `pip install -r requirements.txt`
* Make migrations with

  ```shel
  python manage.py makemigrations
  ```
* Make sure you migrate with

  ```shel
  python manage.py migrate
  ```
* Run these commands to set up the project

  ```shell
  python manage.py bulk_create_roles
  python manage.py init_admin
  python manage.py init_public_client
  ```
* Start the server `python manage.py runserver`
* Open a second terminal window and start celery with `celery -A e_metric_api worker --loglevel=INFO --concurrency=2`
* Open a third terminal window and start celery beat with `celery -A e_metric_api beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler`
