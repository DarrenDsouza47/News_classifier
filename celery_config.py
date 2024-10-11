import dramatiq
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker()
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def classify_article(article):
    from celery_worker import process_article
    return process_article(article)  



