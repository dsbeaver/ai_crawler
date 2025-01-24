import os
import argparse
import redis


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Add a URL to a Redis queue.")
    parser.add_argument("--url", type=str, required=True, help="URL to add to the Redis queue.")
    parser.add_argument("--redis-host", type=str, default=os.getenv("CRAWLER_REDIS_HOST", "localhost"),
                        help="Redis host (default: localhost or $CRAWLER_REDIS_HOST)")
    parser.add_argument("--redis-port", type=int, default=int(os.getenv("CRAWLER_REDIS_PORT", 6379)),
                        help="Redis port (default: 6379 or $CRAWLER_REDIS_PORT)")
    parser.add_argument("--redis-queue", type=str, default=os.getenv("CRAWLER_REDIS_QUEUE", "url_queue"),
                        help="Redis queue name (default: url_queue or $CRAWLER_REDIS_QUEUE)")
    return parser.parse_args()

def main():
    args = parse_args()

    # Connect to Redis
    r = redis.StrictRedis(host=args.redis_host, port=args.redis_port, decode_responses=True)

    # Add the URL to the queue
    r.lpush(args.redis_queue, args.url)
    print(f"URL added to Redis queue '{args.redis_queue}': {args.url}")

if __name__ == "__main__":
    main()
