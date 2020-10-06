# Deployment

Move to working directory.
```sh
$ cd /Users/user/Desktop/nlp_topic_modeling/TopicModeling
```
Activate virtual environment.
```sh
source venv/bin/activate
```
Run broker.
```sh
$ docker run -d --hostname celery-rabbit --name celery-rabbit \
-e RABBITMQ_DEFAULT_USER=username -e RABBITMQ_DEFAULT_PASS=password \
-p 5672:5672 rabbitmq:3.8.8
```

Run celery worker.
```sh
$ celery -A model_testing.run:celery worker --loglevel=info
$ celery -A model_testing.run:celery beat --loglevel=info
```

Run app itself.
```sh
$ python model_testing/run.py
```