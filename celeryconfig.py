from kombu import Exchange, Queue

# Broker settings
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task queues
task_queues = {
    'training_queue': {
        'exchange': 'training_queue',
        'routing_key': 'training',
        'queue_arguments': {'x-max-priority': 10}
    },
    'game_queue': {
        'exchange': 'game_queue',
        'routing_key': 'game',
        'queue_arguments': {'x-max-priority': 10}
    }
}

# Task settings
task_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_concurrency = 2
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 100
worker_max_memory_per_child = 200000  # 200MB

# Task routing
task_routes = {
    'tasks.analyze_training_video': {
        'queue': 'training_queue',
        'routing_key': 'training'
    },
    'tasks.analyze_game_video': {
        'queue': 'game_queue',
        'routing_key': 'game'
    }
}

# Task acknowledgment
task_acks_late = True
task_reject_on_worker_lost = True

# Retry settings
task_default_retry_delay = 300  # 5 minutes
task_max_retries = 3

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s' 