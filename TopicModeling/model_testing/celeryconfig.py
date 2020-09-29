"""
Configure Celery. See the configuration guide at ->
http://docs.celeryproject.org/en/master/userguide/configuration.html#configuration
"""

## Broker settings.
broker_url = 'amqp://username:password@localhost:5672'
# broker_heartbeat = 0

# List of modules to import when the Celery worker starts.
imports = ('model_testing.workers',)

## Using the database to store task state and results.


# result_backend = 'rpc://'
result_backend = 'amqp://username:password@localhost:5672'
# cache_backend = 'memory'
# CELERY_RESULT_BACKEND = 'amqp'
# result_backend = 'memory'
# cache_backend = 'memory'


#'sqlite3:///:memory:'
#result_persistent = False

# accept_content = ['json', 'application/text']
accept_content = ['json', 'pickle']
# result_extended = True
task_track_started = True
result_expires = None
# CELERY_TASK_RESULT_EXPIRES = None

# result_serializer = 'json'
# timezone = "UTC"

# define periodic tasks / cron here
# beat_schedule = {
#    'add-every-10-seconds': {
#        'task': 'workers.add_together',
#        'schedule': 10.0,
#        'args': (16, 16)
#    },
# }

