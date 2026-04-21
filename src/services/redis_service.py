import redis
from django.conf import settings
from redis.connection import ssl


class RedisService:
    def __init__(self):
        self.redis_instance = redis.from_url(settings.CACHES['default']['LOCATION'])

    def set_selected_files(self, conversation_id, file_ids):
        key = f"conversation:{conversation_id}:selected_files"
        # Store file_ids as a comma-separated string
        self.redis_instance.set(key, ",".join(map(str, file_ids)))

    def get_selected_files(self, conversation_id):
        key = f"conversation:{conversation_id}:selected_files"
        file_ids_str = self.redis_instance.get(key)
        if file_ids_str:
            return [int(file_id) for file_id in file_ids_str.decode('utf-8').split(',')]
        return []
