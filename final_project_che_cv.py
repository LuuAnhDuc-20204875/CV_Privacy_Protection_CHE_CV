import os
import win32com.client  # Để xử lý DOCX và DOC
from pdf2image import convert_from_path  # Để xử lý PDF
import shutil
import easyocr
import cv2
import time
import re
import numpy as np
import logging

# Thư mục lưu output cố định
OUTPUT_DIR = r'D:\Timviec365\Text_detection\OUTPUT'

# Đảm bảo thư mục tồn tại
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Tạo logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Tạo file handler ghi log ra file với encoding UTF-8
file_handler = logging.FileHandler('D:\\Timviec365\\Text_detection\\log_processing.txt', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Thêm handler vào logger
logger.addHandler(file_handler)



# Tạo đối tượng reader cho EasyOCR (thêm ngôn ngữ nếu cần)
reader = easyocr.Reader(['en', 'vi'])  # 'en' là tiếng Anh, 'vi' là tiếng Việt

# Chuyển DOCX/DOC sang PDF sử dụng Microsoft Word (Windows Only)
def convert_doc_to_pdf(doc_path, pdf_path):
    try:
        word = win32com.client.Dispatch("Word.Application")
        doc = word.Documents.Open(doc_path)
        word.Visible = False
        # SaveAs2 được dùng thay vì SaveAs
        doc.SaveAs2(pdf_path, FileFormat=17)  # 17 là định dạng PDF
        doc.Saved = True
        doc.Close()
        word.Quit()
    except Exception as e:
        logging.error(f"Đã có lỗi khi chuyển đổi DOC thành PDF: {e}")
        return None
    return pdf_path

# Chuyển đổi PDF thành hình ảnh (JPG hoặc PNG)
def convert_pdf_to_image(pdf_path, output_image_path):
    images = convert_from_path(pdf_path, 300)  # 300 là độ phân giải DPI
    output_images = []
    for page_num, image in enumerate(images):
        output_image = f"{output_image_path}_page_{page_num + 1}.jpg"
        image.save(output_image, 'JPEG')
        output_images.append(output_image)
        logging.info(f"Page {page_num + 1} đã được lưu dưới dạng JPG: {output_image}")

    return output_images

# Kiểm tra thông tin nhạy cảm và che giấu
def process_sensitive_info(image, box, text):
    # Chuyển văn bản về dạng viết thường
    text = text.lower()

    # Định nghĩa các biểu thức chính quy cho thông tin nhạy cảm
    phone_pattern = r'(\+84|0)([.\-\s]?\d){8,10}'

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?'

    website_pattern = r'(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'  # Website chung

    # Thêm các tên miền cụ thể như tuyendung3s.com, viec3s.com, timviec365.vn vào regex
    specific_websites = r'(tuyendung3s\.com|viec3s\.com|timviec365\.vn)'  # Các website cụ thể

    # Thêm các trường hợp chứa 'com' và 'vn' vào danh sách thông tin nhạy cảm
    com_vn_pattern = r'(\.com|\.vn|\bcom\b|\bvn\b|timviec|tuyendung|viec3|vieclam|cuyendung)'

    # Kiểm tra xem đoạn văn bản có chứa thông tin nhạy cảm không
    if re.search(phone_pattern, text) or re.search(email_pattern, text) or re.search(website_pattern, text) or re.search(specific_websites, text) or re.search(com_vn_pattern, text):
        
        logging.info(f"Đã tìm thấy thông tin nhạy cảm: {text}")
        # Nếu tìm thấy thông tin nhạy cảm, xác định màu sắc chiếm ưu thế trong vùng văn bản
        x1, y1 = box[0]
        x2, y2 = box[2]

        region = image[int(y1):int(y2), int(x1):int(x2)]  # Lấy vùng chứa văn bản
        colors, counts = np.unique(region.reshape(-1, 3), axis=0, return_counts=True)  # Đếm màu sắc
        max_count_index = np.argmax(counts)  # Lấy chỉ số màu chiếm ưu thế
        dominant_color = colors[max_count_index]  # Lấy màu chiếm ưu thế

        # Tô màu nền của vùng chứa văn bản bằng màu chiếm ưu thế
        image[int(y1):int(y2), int(x1):int(x2)] = dominant_color  # Tô màu vùng bằng màu chiếm ưu thế
        
        # Vẽ bounding box quanh văn bản
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)  # Vẽ bounding box

        # Hiển thị văn bản lên vùng đã được che giấu
        cv2.putText(image, text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)  # Màu chữ đen


# Xử lý hình ảnh
def process_image(image_path):
    image = cv2.imread(image_path)  # Đọc ảnh
    results = reader.readtext(image)
    return image, results  # Trả về ảnh và kết quả nhận diện

# Xử lý PDF có nhiều trang và ghép tất cả các trang lại thành 1 bức ảnh
def process_pdf(pdf_path):
    images = convert_pdf_to_image(pdf_path, pdf_path)  # Chuyển đổi PDF thành các hình ảnh
    all_images = []
    
    for page_num, image_path in enumerate(images):
        logging.info(f"Đang xử lý trang {page_num + 1} của tài liệu...")
        
        image = cv2.imread(image_path)  # Đọc ảnh
        results = reader.readtext(image)  # Nhận diện văn bản
        
        for result in results:
            box, text, confidence = result
            process_sensitive_info(image, box, text)  # Kiểm tra và che thông tin nhạy cảm

        all_images.append(image)  # Lưu lại ảnh đã xử lý

    # Ghép tất cả các trang lại thành 1 bức ảnh duy nhất
    final_image = np.vstack(all_images)  # Ghép các ảnh theo chiều dọc
    final_output_path = os.path.join(OUTPUT_DIR, 'final_output_pdf.jpg')
    cv2.imwrite(final_output_path, final_image)

    logging.info(f"Đã lưu ảnh che xong tại: {final_output_path} ")
    print(f"Đã lưu ảnh che xong tại: {final_output_path} ")


# Xử lý DOCX/DOC thành PDF và chuyển thành hình ảnh
def process_doc(doc_path, output_folder):
    # Chuyển DOC/DOCX thành PDF tạm thời
    pdf_path = os.path.join(output_folder, 'temp.pdf')
    convert_doc_to_pdf(doc_path, pdf_path)

    # Chuyển PDF thành hình ảnh
    images = convert_pdf_to_image(pdf_path, output_folder)  # Chuyển đổi PDF thành các hình ảnh
    all_images = []

    for image_path in images:
        image = cv2.imread(image_path)  # Đọc ảnh
        results = reader.readtext(image)  # Nhận diện văn bản
        
        for result in results:
            box, text, confidence = result
            process_sensitive_info(image, box, text)  # Kiểm tra và che thông tin nhạy cảm

        all_images.append(image)  # Lưu lại ảnh đã xử lý

    # Ghép tất cả các trang lại thành 1 bức ảnh duy nhất
    final_image = np.vstack(all_images)  # Ghép các ảnh theo chiều dọc

    final_output_path = os.path.join(OUTPUT_DIR, 'final_output_doc.jpg')
    cv2.imwrite(final_output_path, final_image)

    # Xóa tệp PDF tạm thời sau khi đã chuyển thành hình ảnh
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        print("Tệp PDF tạm thời đã được xóa.")
        
# Xử lý các loại tệp khác nhau
def process_file(file_path, output_folder):
    extension = file_path.split('.')[-1].lower()

    if extension == "pdf":
        try:
            process_pdf(file_path)  # Xử lý PDF
        except Exception as e:
            logging.exception(f"Lỗi khi xử lý pdf: {e}")

    elif extension == "docx" or extension == "doc":
        try:
            process_doc(file_path, output_folder)  # Gọi hàm xử lý DOCX/DOC
        except Exception as e:
            logging.exception(f"Lỗi khi xử lý doc: {e}")

    elif extension in ['jpg', 'jpeg', 'png']:
        image, results = process_image(file_path)  # Xử lý hình ảnh
        for result in results:
            box, text, confidence = result
            process_sensitive_info(image, box, text)

        # ✅ Lưu lại ảnh đã xử lý
        final_output_path = os.path.join(OUTPUT_DIR, 'final_output_img.jpg')
        cv2.imwrite(final_output_path, image)
        print(f"Ảnh đã xử lý được lưu tại: {final_output_path}")

    else:
        print("Định dạng tệp không được hỗ trợ")


if __name__ == "__main__":
    # Bắt đầu đo thời gian

    # Nhập đường dẫn file cần xử lý từ người dùng
    file_path = input("Nhập đường dẫn đầy đủ đến file cần xử lý (có thể là .docx, .pdf, .jpg, .png...): ").strip()

    # Thiết lập thư mục output mặc định
    output_folder = r'D:\Timviec365\Text_detection\cv_doc_to_img'

    start_time = time.time()
    # Gọi hàm xử lý file
    process_file(file_path, output_folder)

    # Kết thúc đo thời gian
    end_time = time.time()
    processing_time = end_time - start_time
    logging.info(f"Tổng thời gian xử lý ảnh: {processing_time:.4f} giây")
    print(f"Tổng thời gian xử lý ảnh: {processing_time:.4f} giây")

