"""OpenAI API integration for extracting data from screenshots."""

import base64
import re
from pathlib import Path
from textwrap import dedent

from openai import OpenAI

from config import Settings


class OpenAIExtractor:
    """Extracts structured data from images using OpenAI Vision API."""

    def __init__(self, api_key: str = Settings.OPENAI_API_KEY):
        """
        Initialize OpenAI extractor.

        Args:
            api_key: OpenAI API key (defaults to Settings.OPENAI_API_KEY)
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = OpenAI(api_key=self.api_key)
        self.model = Settings.OPENAI_MODEL

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_data(
        self,
        image_path: Path,
        prompt: str,
        additional_context: str | None = None
    ) -> str:
        """
        Extract data from an image using OpenAI Vision.

        Args:
            image_path: Path to the image file
            prompt: Extraction prompt describing what data to extract
            additional_context: Optional additional context for the extraction

        Returns:
            Extracted data as a string
        """
        base64_image = self._encode_image(image_path)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an e-commerce product data extraction specialist. "
                    "Your task is to identify and extract information about the MAIN product "
                    "on product detail pages. Focus on the product with the largest image "
                    "and whose name appears in the page heading. Ignore small thumbnails in "
                    "'shop similar' or 'recommended' carousels. "
                    "You MUST always provide extracted data - use your best judgment for "
                    "unusual layouts like resale marketplaces (GOAT, StockX) where prices "
                    "may be shown per size or as 'Lowest Ask'."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nContext: {additional_context}" if additional_context else prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000
        )

        return response.choices[0].message.content or ""

    def extract_product_info(self, image_path: Path) -> dict:
        """
        Extract product information from a screenshot.

        Args:
            image_path: Path to the product screenshot

        Returns:
            Dictionary with product information
        """
        prompt = dedent("""
            Extract product information from the MAIN PRODUCT on this e-commerce page.

            IDENTIFYING THE MAIN PRODUCT:
            The main product is the one being sold on this page. Look for:
            - The product name in the page title or largest heading
            - The largest product image (usually left or center of the page)
            - The product with detailed description, size selector, or "Add to Cart" button

            DO NOT extract from these secondary sections:
            - "Shop similar" / "Similar products" horizontal carousels
            - "You may also like" / "Recommended" sections
            - Small product thumbnails in rows at the top of the page

            HANDLING DIFFERENT PRICE FORMATS:
            - Standard: Look for a single price near the product name
            - Resale sites (StockX, GOAT): Look for "Lowest Ask", "Buy Now" price, or the starting price shown. If prices vary by size, use the lowest visible price or the one currently selected
            - Auction/bid sites: Use the "Buy Now" or "Lowest Ask" price, not bids
            - Pre-owned/Refurbished (Walmart, Amazon): The main product may show "Pre-Owned" or "Refurbished" - this is still the main product if it has the largest image

            ALWAYS EXTRACT DATA - even if the layout is unusual, identify the main product and extract what you can find.

            Extract these details:
            1. Product name/title (the full name from the heading, not abbreviated)
            2. Original price (if shown crossed out, otherwise N/A)
            3. Sale/current price (the price to pay now - use lowest available if multiple sizes shown)
            4. Currency (USD, EUR, GBP, etc.)
            5. Discount percentage (if shown, otherwise N/A)

            Return the data in this exact format:
            PRODUCT_NAME: <value>
            ORIGINAL_PRICE: <value or N/A>
            SALE_PRICE: <value or N/A>
            CURRENCY: <value>
            DISCOUNT_PERCENT: <value or N/A>
        """).strip()

        response = self.extract_data(image_path, prompt)
        return self._parse_product_response(response)

    def _parse_product_response(self, response: str) -> dict:
        """Parse the product extraction response into a dictionary."""
        result = {
            "product_name": None,
            "original_price": None,
            "sale_price": None,
            "currency": None,
            "discount_percent": None,
            "raw_response": response
        }

        lines = response.strip().split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if value.upper() == "N/A":
                    value = None

                if key in ["product_name", "currency"]:
                    result[key] = value
                elif key in ["original_price", "sale_price"]:
                    result[key] = self._parse_price(value)
                elif key == "discount_percent":
                    result["discount_percent"] = self._parse_percentage(value)

        return result

    def _parse_price(self, value: str | None) -> float | None:
        """Parse a price string to float, handling various currency formats."""
        if not value:
            return None
        try:
            # Extract the numeric part (handles formats like "27.77", "1,234.56", "EUR 19.43")
            match = re.search(r'[\d,]+\.?\d*', value)
            if match:
                number_str = match.group().replace(",", ".")
                return float(number_str)
            return None
        except (ValueError, AttributeError):
            return None

    def _parse_percentage(self, value: str | None) -> float | None:
        """Parse a percentage string to float."""
        if not value:
            return None
        try:
            cleaned = value.replace("%", "").replace("-", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def calculate_final_price(self, product_info: dict) -> float | None:
        """
        Calculate the final sale price from extracted product info.

        Args:
            product_info: Dictionary with product information

        Returns:
            Final price as float, or None if cannot be determined
        """
        # If sale price is directly available, use it
        if product_info.get("sale_price") is not None:
            return product_info["sale_price"]

        # Calculate from original price and discount
        original = product_info.get("original_price")
        discount = product_info.get("discount_percent")

        if original is not None and discount is not None:
            return round(original * (1 - discount / 100), 2)

        # Fall back to original price if no discount
        return original
