import os
import re
from PIL import Image
import pytesseract

def image_to_text(image_path):
    """Convert image to text using OCR."""
    text = pytesseract.image_to_string(Image.open(image_path))
    words = re.findall(r'\b\w+\b', text)
    return words

def convert_directory_images_to_text_list(dir_path):
    """Convert all images in a directory to a list of texts."""
    words = []

    for file_name in os.listdir(dir_path):
        if file_name.endswith('.jpg') or file_name.endswith('.png'):  # Add or change file types if needed
            image_path = os.path.join(dir_path, file_name)
            words_in_image = image_to_text(image_path)
            words.extend(words_in_image)

            print(words_in_image)

    return words

# Directory to process
dir_path = "/Users/samsavage/Desktop/imagestuff"  # Change to your directory

word_list = convert_directory_images_to_text_list(dir_path)

# Save words to a file
with open('words.txt', 'w') as f:
    f.write(", ".join(word_list))

