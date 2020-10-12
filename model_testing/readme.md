# Deployment

#### Configuration
Application configuration, including the database and message broker connection strings, default admin data, is defined in `model_testing/config.py` and `celery/config.py`.

#### Requirements
Necessary: RabbitMQ, Docker, Celery, PostgreSQL.

Optional: nvidia-smi, nvcc.

##### Installing python dependencies:
Create virtual environment.
```sh
python -m venv env
```

Activate virtual environment.
```sh
[win] .\env\Scripts\activate
[mac] source venv/bin/activate
```
Install requirements.
```sh
pip install -r requirements.txt --no-cache-dir
```


#### Run
With `env` started:

Ensure your PostgreSQL database is running.

Run broker.
```sh
docker run -d --hostname celery-rabbit --name celery-rabbit -e RABBITMQ_DEFAULT_USER=username -e RABBITMQ_DEFAULT_PASS=password -p 5672:5672 rabbitmq:3.8.8
```

Run celery worker and beat (for delayed tasks) in separate terminals.
```sh
celery -A run:celery worker --loglevel=INFO
celery -A run:celery beat --loglevel=INFO
```

Run app itself.
```sh
python run.py
```