import redis
import os
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

class RedisService:
    # def __init__(self):
    #     redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    #     redis_password = os.getenv('REDIS_PASSWORD', '')
    #
    #     try:
    #         if redis_password:
    #             if '@' not in redis_url and 'redis://' in redis_url:
    #                 redis_url = f"redis://:{redis_password}@localhost:6379/0"
    #
    #         self.redis_instance = redis.from_url(redis_url, decode_responses=True)
    #         self.redis_instance.ping()
    #         logger.info("Redis connected successfully")
    #
    #     except Exception as e:
    #         logger.error(f"Redis connection failed: {e}")
    #         try:
    #             self.redis_instance = redis.Redis(
    #                 host='localhost',
    #                 port=6379,
    #                 db=0,
    #                 password=redis_password,
    #                 decode_responses=True
    #             )
    #             self.redis_instance.ping()
    #             logger.info("Redis connected with password")
    #         except Exception as e2:
    #             logger.error(f"Redis fallback failed: {e2}")
    #             self.redis_instance = None

    def __init__(self):
        self.redis_instance = redis.from_url(settings.CACHES['default']['LOCATION'])

    def set_selected_files(self, conversation_id, file_ids):
        if not self.redis_instance:
            return
        
        try:
            key = f"conversation:{conversation_id}:selected_files"
            self.redis_instance.set(key, ",".join(map(str, file_ids)))
        except Exception as e:
            logger.error(f"Error setting files: {e}")

    def get_selected_files(self, conversation_id):
        if not self.redis_instance:
            return []
        
        try:
            key = f"conversation:{conversation_id}:selected_files"
            file_ids_str = self.redis_instance.get(key)
            if file_ids_str:
                return [int(file_id) for file_id in file_ids_str.split(',') if file_id]
            return []
        except Exception as e:
            logger.error(f"Error getting files: {e}")
            return []