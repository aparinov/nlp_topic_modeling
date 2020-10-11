imports = ('model_testing.workers',)

broker_url = 'amqp://username:password@localhost:5672'
result_backend = 'amqp://username:password@localhost:5672'

accept_content = ['json', 'pickle']

task_track_started = True
result_expires = None
enable_utc = True