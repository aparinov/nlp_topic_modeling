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
$ celery -A model_testing.run:celery worker --loglevel=info
```

Run celery worker.
```sh
$ docker run -d --hostname celery-rabbit --name celery-rabbit \
-e RABBITMQ_DEFAULT_USER=username -e RABBITMQ_DEFAULT_PASS=password \
-p 5672:5672 rabbitmq:3.8.8
```

Run app itself.
```sh
$ celery -A model_testing.run:celery worker --loglevel=info
```