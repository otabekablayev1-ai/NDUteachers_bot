from pdf2image import convert_from_path

def pdf_to_images(file_path):
    return convert_from_path(file_path)