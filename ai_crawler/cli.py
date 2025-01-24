import os
import asyncio
import argparse
import redis
import logging
from ai_crawler.ai_crawler import * 
import json
import datetime


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="AI Crawler: Process URLs or run as a daemon.")
    
    # Common arguments
    parser.add_argument("--output-dir", type=str, default=os.getenv("CRAWLER_OUTPUT_DIR", "./output"),
                        help="Directory to save output JSON files (default: ./output or $CRAWLER_OUTPUT_DIR)")
    parser.add_argument("--project-name", type=str, default=os.getenv("CRAWLER_PROJECT_NAME", "ai_crawler"),
                        help="Name of the project (default: ai_crawler or $CRAWLER_PROJECT_NAME)")

    # Daemon mode arguments
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode, processing URLs from a Redis queue.")
    parser.add_argument("--redis-host", type=str, default=os.getenv("CRAWLER_REDIS_HOST", "localhost"),
                        help="Redis host (default: localhost or $CRAWLER_REDIS_HOST)")
    parser.add_argument("--redis-port", type=int, default=int(os.getenv("CRAWLER_REDIS_PORT", 6379)),
                        help="Redis port (default: 6379 or $CRAWLER_REDIS_PORT)")
    parser.add_argument("--redis-queue", type=str, default=os.getenv("CRAWLER_REDIS_QUEUE", "url_queue"),
                        help="Redis queue name (default: url_queue or $CRAWLER_REDIS_QUEUE)")
    parser.add_argument("--failed-queue", type=str, default=os.getenv("CRAWLER_FAILED_QUEUE", "failed_queue"),
                        help="Redis failed queue name (default: failed_queue or $CRAWLER_FAILED_QUEUE)")
    parser.add_argument("--log-file", type=str, default=os.getenv("CRAWLER_LOG_FILE", "./crawler.log"),
                        help="Path to log file (default: ./crawler.log or $CRAWLER_LOG_FILE)")

    # Command-line mode arguments
    parser.add_argument("--url", type=str, help="URL to process in command-line mode.")

    return parser.parse_args()


def configure_logging(log_file: str):
    """Set up logging configuration."""
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


async def daemon_mode(redis_host, redis_port, redis_queue, failed_queue, output_dir, project_name):
    """Run the crawler as a daemon, reading URLs from a Redis queue."""
    logging.info(f"Starting daemon mode with Redis at {redis_host}:{redis_port}, queue: {redis_queue}")
    r = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    crawler = AICrawler(output_dir=output_dir, project_name=project_name)

    while True:
        url = r.rpop(redis_queue)  # Fetch URL from Redis queue
        if url:
            logging.info(f"Processing URL from queue: {url}")
            try:
                await crawler.process_url(url)
            except Exception as e:
                logging.error(f"Failed to process URL: {url}, Error: {e}")
                failure_message = {
                    "url": url,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                r.lpush(failed_queue, json.dumps(failure_message))
        else:
            await asyncio.sleep(1)  # Wait for new URLs to arrive


async def command_line_mode(url, output_dir, project_name):
    """Process a single URL in command-line mode."""
    print(f"Processing URL: {url}")
    crawler = AICrawler(output_dir=output_dir, project_name=project_name)
    await crawler.process_url(url)


def main():
    args = parse_args()

    # Configure logging
    if args.daemon:
        configure_logging(args.log_file)

    if args.daemon:
        # Daemon mode
        asyncio.run(daemon_mode(
            redis_host=args.redis_host,
            redis_port=args.redis_port,
            redis_queue=args.redis_queue,
            failed_queue=args.failed_queue,
            output_dir=args.output_dir,
            project_name=args.project_name
        ))
    elif args.url:
        # Command-line mode
        asyncio.run(command_line_mode(
            url=args.url,
            output_dir=args.output_dir,
            project_name=args.project_name
        ))
    else:
        print("You must specify either --daemon or --url.")
        exit(1)


if __name__ == "__main__":
    main()
