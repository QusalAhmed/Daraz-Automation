import os
from PIL import Image


def convert_webp_to_jpg(input_path, output_path):
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")
        img.save(output_path, "JPEG")
    except Exception as e:
        print(f"Error converting image: {e}")


def process_folders(root_folder, destination_root):
    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.webp'):
                webp_path = os.path.join(foldername, filename)
                jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                jpg_path = os.path.join(destination_root, foldername, jpg_filename)

                os.makedirs(os.path.dirname(jpg_path), exist_ok=True)
                convert_webp_to_jpg(webp_path, jpg_path)
                os.remove(webp_path)


if __name__ == "__main__":
    root_folder = 'D:\\Downloads\\Business\\Rabit Earphone\\Shopee Rabbit'  # Replace with the root folder path
    destination_root = 'D:\\Downloads\\Business\\Rabit Earphone\\Shopee Rabbit JPG'  # Replace with the destination folder path

    process_folders(root_folder, destination_root)
