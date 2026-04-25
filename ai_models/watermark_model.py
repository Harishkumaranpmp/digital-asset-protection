"""
SportShield — Watermark Model
Implements invisible LSB (Least Significant Bit) watermarking for digital assets.
"""

import logging
from typing import Optional
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class WatermarkModel:
    """
    Handles embedding and extracting invisible watermarks in image assets.
    This allows us to track the origin of a file even if it has been modified.
    """

    @staticmethod
    def embed(image_path: str, watermark_id: str, output_path: str) -> bool:
        """
        Embed a unique ID into an image using LSB steganography.
        
        Args:
            image_path (str): Path to original image.
            watermark_id (str): Unique string to embed.
            output_path (str): Where to save the watermarked image.
            
        Returns:
            bool: Success status.
        """
        if not PIL_AVAILABLE:
            logging.error("PIL not available for watermarking.")
            return False

        try:
            img = Image.open(image_path).convert("RGB")
            pixels = list(img.getdata())

            # Convert watermark_id to binary string (8 bits per char)
            binary_data = ''.join(format(ord(c), '08b') for c in watermark_id[:32])
            binary_data += '00000000'  # Null terminator to know where to stop reading

            modified_pixels = []
            data_idx = 0

            for pixel in pixels:
                r, g, b = pixel
                if data_idx < len(binary_data):
                    # Modify the Least Significant Bit (LSB) of the Blue channel
                    # This change is invisible to the human eye but readable by code.
                    b = (b & ~1) | int(binary_data[data_idx])
                    data_idx += 1
                modified_pixels.append((r, g, b))

            img.putdata(modified_pixels)
            img.save(output_path)
            return True

        except Exception as e:
            logging.error(f"Watermark embedding failed: {e}")
            return False

    @staticmethod
    def extract(image_path: str, max_length: int = 32) -> Optional[str]:
        """
        Extract the invisible ID from a watermarked image.
        
        Args:
            image_path (str): Path to the image file.
            max_length (int): Maximum characters to extract.
            
        Returns:
            Optional[str]: The extracted watermark ID if found.
        """
        if not PIL_AVAILABLE:
            return None

        try:
            img = Image.open(image_path).convert("RGB")
            pixels = list(img.getdata())

            binary_data = ""
            # Each character is 8 bits, plus the 8-bit null terminator
            bit_limit = (max_length * 8) + 8
            
            for pixel in pixels[:bit_limit]:
                # Extract the LSB from the Blue channel
                binary_data += str(pixel[2] & 1)

            # Convert binary bits back into characters
            chars = []
            for i in range(0, len(binary_data), 8):
                byte = binary_data[i:i+8]
                if byte == '00000000': # Stop at null terminator
                    break
                chars.append(chr(int(byte, 2)))

            extracted_id = ''.join(chars)
            return extracted_id if extracted_id else None

        except Exception as e:
            logging.error(f"Watermark extraction failed: {e}")
            return None
