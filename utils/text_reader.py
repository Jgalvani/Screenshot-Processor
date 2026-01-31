"""Text file reader utility for extracting URLs."""

import re
from pathlib import Path


class TextReader:
    """Reads and extracts URLs from text files."""

    URL_PATTERN = re.compile(
        r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"
        r"(?:/[-\w%!$&'()*+,./:;=?@~#]*)*"
    )

    def __init__(self, file_path: str | Path):
        """
        Initialize TextReader with a file path.

        Args:
            file_path: Path to the text file (.txt)
        """
        self.file_path = Path(file_path)
        self._validate_file()

    def _validate_file(self) -> None:
        """Validate that the file exists and is a .txt file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        if self.file_path.suffix.lower() != ".txt":
            raise ValueError(f"Expected .txt file, got: {self.file_path.suffix}")

    def extract_urls(self) -> list[str]:
        """
        Extract all URLs from the text file.

        Supports two formats:
        - One URL per line
        - URLs embedded in text (extracted via regex)

        Returns:
            List of unique URLs found in the file
        """
        urls = set()

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    # Skip empty lines and comments
                    continue

                # Try to match URLs in the line
                found_urls = self.URL_PATTERN.findall(line)
                urls.update(found_urls)

        return list(urls)
