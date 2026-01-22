# Screenshot Processor - Browser Automation Workflow

A Python Playwright-based browser automation tool that reads URLs from Word documents, captures screenshots, and extracts data using OpenAI Vision API.

## Features

- **URL Extraction**: Reads URLs from Microsoft Word (.docx) files
- **Human-like Browsing**: Simulates realistic browser behavior with random delays and mouse movements
- **Screenshot Capture**: Full-page and element-specific screenshot capabilities
- **Image Cropping**: Crop screenshots to specific regions or elements
- **AI Data Extraction**: Uses OpenAI Vision API to extract structured data from screenshots
- **Price Calculation**: Automatically calculates final sale prices from extracted product data
- **Sequential Processing**: Processes URLs one-by-one to maintain reliability

## Project Structure

```
screenshot_saver/
├── config/                  # Configuration module
│   ├── __init__.py
│   └── settings.py          # Centralized settings
├── data/                    # Input data (Word files)
├── output/                  # Output screenshots and results
├── pages/                   # Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py         # Base page class with common functionality
│   └── generic_page.py      # Generic page handler for any URL
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── word_reader.py       # Word document URL extraction
│   ├── screenshot_handler.py # Screenshot capture and manipulation
│   ├── openai_extractor.py  # OpenAI Vision data extraction
│   └── human_behavior.py    # Human-like browser behavior simulation
├── main.py                  # Main orchestrator script
├── .env.example             # Environment variables template
├── Pipfile                  # Pipenv dependencies
├── requirements.txt         # Pip requirements
└── README.md
```

## Prerequisites

- Python 3.10+
- pipenv
- OpenAI API key

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd screenshot_saver
   ```

2. **Install dependencies using pipenv**:
   ```bash
   pipenv install
   ```

3. **Install Playwright browsers**:
   ```bash
   pipenv run playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

1. Place your Word document containing URLs in the `data/` folder

2. Create and enter a Python virtual environment:
```bash
pipenv shell
```

3. Run the automation:
```bash
python main.py
```

4. Or specify a Word file directly:
```bash
python main.py /path/to/your/document.docx
```

### Output

- Screenshots are saved in the `output/` folder
- Results are saved as JSON files with timestamp

## Configuration

All settings can be configured via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` |
| `BROWSER_HEADLESS` | Run browser without UI | `false` |
| `BROWSER_SLOW_MO` | Delay between actions (ms) | `100` |
| `VIEWPORT_WIDTH` | Browser viewport width | `1920` |
| `VIEWPORT_HEIGHT` | Browser viewport height | `1080` |
| `SCREENSHOT_FORMAT` | Image format (png/jpeg) | `png` |
| `SCREENSHOT_FULL_PAGE` | Capture full page | `false` |
| `MIN_ACTION_DELAY` | Min delay between actions (ms) | `500` |
| `MAX_ACTION_DELAY` | Max delay between actions (ms) | `2000` |
| `PAGE_LOAD_TIMEOUT` | Page load timeout (ms) | `30000` |

## Architecture

### Page Object Model (POM)

The project follows the Page Object Model pattern for maintainable and reusable code:

- **BasePage**: Contains common page interactions (navigation, screenshots, clicks)
- **GenericPage**: Extends BasePage for handling any URL with data extraction

### Utilities

- **WordReader**: Extracts URLs from Word documents using python-docx
- **ScreenshotHandler**: Captures and manipulates screenshots using Pillow
- **OpenAIExtractor**: Extracts structured data from images via OpenAI Vision API
- **HumanBehavior**: Simulates human-like mouse movements and delays

## Example Word Document Format

Create a Word document with URLs in any format:
- Plain text URLs: `https://example.com/product/123`
- Hyperlinks: Click-able links
- URLs in tables

The tool will automatically extract all valid URLs from the document.

## API Reference

### WordReader

```python
from utils import WordReader

reader = WordReader("path/to/document.docx")
urls = reader.extract_urls()  # Returns list of URLs
```

### ScreenshotHandler

```python
from utils import ScreenshotHandler

handler = ScreenshotHandler()
screenshot_path = handler.capture(page, name="my_screenshot")
cropped_path = handler.crop(screenshot_path, (x1, y1, x2, y2))
```

### OpenAIExtractor

```python
from utils import OpenAIExtractor

extractor = OpenAIExtractor()
product_info = extractor.extract_product_info(screenshot_path)
final_price = extractor.calculate_final_price(product_info)
```

## License

This project is for demonstration and testing purposes.
