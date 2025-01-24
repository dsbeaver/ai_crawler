# AI Crawler

AI Crawler is a simple wrapper for the crawl4ai package.  

- [GitHub Repository - crawl4ai](https://github.com/unclecode/crawl4ai)  
- [Documentation - crawl4ai](https://docs.crawl4ai.com/)

## Key Features

- Crawls web pages asynchronously for high performance.
- Automatically parses sitemap XMLs to discover more URLs to crawl.
- Outputs the content of each web page in a JSON file, with additional metadata.
- Can be run in daemon mode, continuously processing URLs from a Redis queue.
- Handles failures gracefully, moving failed URLs to a separate Redis queue.
- All configurations can be set either via command-line arguments or environment variables.

## Installation

To install AI Crawler, you need to have Python 3.6 or higher installed on your system. 

1. Clone this repository:
    ```bash
    git clone https://github.com/your_username/ai_crawler.git
    ```
2. Navigate to the project directory:
    ```bash
    cd ai_crawler
    ```
3. Build the project using `poetry`:
    ```bash
    poetry build
    ```
4. Install the generated package:
    ```bash
    pip install dist/ai_crawler-0.1.0-py3-none-any.whl
    ```

## Configuration 

You can configure AI Crawler via command-line arguments or environment variables. The following environment variables are available:

- `CRAWLER_REDIS_HOST`: Redis host (default: `localhost`)
- `CRAWLER_REDIS_PORT`: Redis port (default: `6379`)
- `CRAWLER_REDIS_QUEUE`: Redis queue name for URLs (default: `url_queue`)
- `CRAWLER_FAILED_QUEUE`: Redis queue name for failed URLs (default: `failed_queue`)
- `CRAWLER_OUTPUT_DIR`: Directory to save output JSON files (default: `./output`)
- `CRAWLER_PROJECT_NAME`: Name of the project (default: `ai_crawler`)
- `CRAWLER_LOG_FILE`: Path to log file (default: `./crawler.log`)

## Usage

### Command-line Mode

To process a single URL, use the `--url` argument:

```bash
ai_crawler --url http://example.com
```

### Daemon Mode

To run AI Crawler in daemon mode, set the `--daemon` flag:

```bash
ai_crawler --daemon
```

## Directory Structure

```
ai_crawler/
    pyproject.toml
    .gitignore
    env_template
    LICENSE
    README.md
    ai_crawler/
        __init__.py
        put_on_queue.py
        ai_crawler.py
        cli.py
```

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

## License

AI Crawler is licensed under the terms of the [MIT License](LICENSE).

## Note 

This README.md was generated using chatgpt.
