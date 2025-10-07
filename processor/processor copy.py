import os
import win32com.client  # Để xử lý DOCX và DOC
from pdf2image import convert_from_path  # Để xử lý PDF
import cv2
import re
import numpy as np
import easyocr
import logging
import traceback
import pythoncom  # thêm dòng này ở đầu file nếu chưa có

# Tạo logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('D:\\Timviec365\\Text_detection\\log_processing.txt', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

reader = easyocr.Reader(['en', 'vi'])

def resize_if_large(image, image_path=None, max_width=1400, save_preview=False):
    """
    Resize ảnh nếu chiều rộng lớn hơn max_width.
    Nếu image_path được truyền và save_preview=True thì lưu ảnh đã resize.
    Trả về ảnh đã resize và (nếu có) đường dẫn ảnh preview.
    """
    if image.shape[1] > max_width:
        scale = max_width / image.shape[1]
        image_resized = cv2.resize(image, None, fx=scale, fy=scale)
        print(f"🔧 Ảnh đã được resize từ {image.shape} -> {image_resized.shape}")
        
        preview_path = None
        if save_preview and image_path:
            preview_path = image_path.replace(".jpg", "_resized.jpg")
            cv2.imwrite(preview_path, image_resized)
            print(f"💾 Ảnh preview đã lưu tại: {preview_path}")
        
        return image_resized, preview_path
    else:
        return image, None


def convert_doc_to_pdf(doc_path, pdf_path):
    try:
        abs_doc_path = os.path.abspath(doc_path)
        abs_pdf_path = os.path.abspath(pdf_path)

        print(f"📄 Bắt đầu chuyển đổi DOC/DOCX sang PDF: {abs_doc_path}")
        pythoncom.CoInitialize()

        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(abs_doc_path)
        doc.SaveAs2(abs_pdf_path, FileFormat=17)
        doc.Saved = True
        doc.Close()
        word.Quit()

        print(f"✅ Đã chuyển thành PDF: {abs_pdf_path}")
        return abs_pdf_path

    except Exception as e:
        print(f"❌ Lỗi chuyển đổi DOC/DOCX sang PDF: {e}")
        logging.error(f"Lỗi chuyển đổi DOC sang PDF: {e}")
        traceback.print_exc()
        return None

    finally:
        pythoncom.CoUninitialize()



def convert_pdf_to_image(pdf_path, output_image_path):
    try:
        print(f"📄 Bắt đầu chuyển PDF sang ảnh: {pdf_path}")
        images = convert_from_path(pdf_path, 300)  # 300 DPI
    except Exception as e:
        logging.error(f"Lỗi chuyển PDF sang ảnh: {e}")
        print(f"❌ Lỗi chuyển PDF sang ảnh: {e}")
        traceback.print_exc()
        raise

    output_images = []
    for page_num, image in enumerate(images):
        output_image = f"{output_image_path}_page_{page_num + 1}.jpg"
        image.save(output_image, 'JPEG')
        output_images.append(output_image)
        logging.info(f"✅ Page {page_num + 1} đã được lưu dưới dạng JPG: {output_image}")
        print(f"✅ Page {page_num + 1} đã được lưu dưới dạng JPG: {output_image}")

    return output_images



def process_sensitive_info(image, box, text):
    try:
        text_lower = text.lower()
        phone_pattern = r'(\+84|0)([.\-\s]?\d){8,10}'
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?'
        website_pattern = r'(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        specific_websites = r'(tuyendung3s\.com|viec3s\.com|timviec365\.vn)'
        com_vn_pattern = r'(\.com|\.vn|\bcom\b|\bvn\b|timviec|tuyendung|viec3|vieclam|cuyendung)'

        if re.search(phone_pattern, text_lower) or \
           re.search(email_pattern, text_lower) or \
           re.search(website_pattern, text_lower) or \
           re.search(specific_websites, text_lower) or \
           re.search(com_vn_pattern, text_lower):

            print(f"🔒 [MASK] Phát hiện thông tin nhạy cảm: {text}")
            logging.info(f"Thông tin nhạy cảm: {text}")

            x1, y1 = box[0]
            x2, y2 = box[2]

            region = image[int(y1):int(y2), int(x1):int(x2)]
            colors, counts = np.unique(region.reshape(-1, 3), axis=0, return_counts=True)
            dominant_color = colors[np.argmax(counts)]
            image[int(y1):int(y2), int(x1):int(x2)] = dominant_color
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.putText(image, text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    except Exception as e:
        print(f"❌ [MASK] Lỗi khi xử lý vùng nhạy cảm: {text}")
        traceback.print_exc()



def process_image(image_path):
    print(f"📥 [IMG] Đang đọc ảnh: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise Exception(f"❌ Không đọc được ảnh từ file: {image_path}")
    print(f"✅ Ảnh đã được load: {image.shape}")

    # Resize nếu ảnh quá lớn
    image, preview_path = resize_if_large(image, image_path, save_preview=True)

    print("🔎 Bắt đầu OCR...")
    results = reader.readtext(image)
    print(f"🔍 OCR phát hiện {len(results)} vùng văn bản.")
    return image, results



def process_pdf(pdf_path, output_path):
    print(f"\n🚀 [PDF] Bắt đầu xử lý PDF: {pdf_path}")
    try:
        print(f"📄 Bắt đầu chuyển PDF sang ảnh: {pdf_path}")
        images = convert_pdf_to_image(pdf_path, pdf_path)
    except Exception as e:
        print("❌ Lỗi quá trình xử lý PDF thành ảnh ....")
        logging.error(f"Lỗi khi xử lý PDF: {e}")
        traceback.print_exc()
        return  # Dừng hẳn, không xử lý tiếp

    all_images = []
    for idx, image_path in enumerate(images):
        print(f"🔄 [PDF] Đang xử lý trang {idx + 1}: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise Exception(f"❌ Không đọc được ảnh từ file: {image_path}")

        # Resize nếu ảnh quá lớn
        image, preview_path = resize_if_large(image, image_path, save_preview=True)

        results = reader.readtext(image)
        print(f"🔍 Trang {idx + 1}: {len(results)} vùng văn bản được phát hiện")

        for result in results:
            box, text, _ = result
            process_sensitive_info(image, box, text)
        all_images.append(image)

    try:
        final_image = np.vstack(all_images)
        cv2.imwrite(output_path, final_image)
        print(f"✅ Đã lưu kết quả sau khi xử lý PDF vào: {output_path}")
    except Exception as e:
        logging.error(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
        print(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
        traceback.print_exc()

    
    # Sau khi đã lưu file kết quả, tiến hành xóa các ảnh trung gian
    try:
        for image_path in images:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"🧹 Đã xóa ảnh gốc: {image_path}")

            preview_path = image_path.replace(".jpg", "_resized.jpg")
            if os.path.exists(preview_path):
                os.remove(preview_path)
                print(f"🧹 Đã xóa ảnh preview: {preview_path}")
    except Exception as e:
        logging.error(f"❌ Lỗi khi xóa file tạm: {e}")
        print(f"❌ Lỗi khi xóa file tạm: {e}")
        traceback.print_exc()




def process_doc(doc_path, output_path):
    print(f"\n📘 [WORD] Bắt đầu xử lý tệp Word: {doc_path}")
    temp_pdf = os.path.join(os.path.dirname(output_path), 'temp.pdf')

    # Bước 1: Chuyển Word sang PDF
    converted_pdf = convert_doc_to_pdf(doc_path, temp_pdf)
    if not converted_pdf or not os.path.exists(converted_pdf):
        print("❌ Không thể chuyển Word sang PDF. Dừng xử lý.")
        return

    # Bước 2: Xử lý PDF như bình thường
    try:
        process_pdf(converted_pdf, output_path)
    except Exception as e:
        print(f"❌ Lỗi xử lý PDF sau khi chuyển từ Word: {e}")
        logging.error(f"Lỗi xử lý PDF từ Word: {e}")
        traceback.print_exc()

    # Bước 3: Dọn dẹp file tạm
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
        print("🧹 Đã xóa file tạm PDF sau xử lý.")


def process_file(file_path, output_path):
    ext = file_path.split('.')[-1].lower()
    print(f"\n📂 Đang xử lý file: {file_path}")
    print(f"📄 Định dạng: {ext}")

    try:
        if ext == 'pdf':
            print("📘 Phát hiện PDF. Gọi hàm process_pdf()...")
            process_pdf(file_path, output_path)
            print(f"✅ PDF đã xử lý xong và lưu tại: {output_path}")

        elif ext in ['doc', 'docx']:
            print("📝 Phát hiện Word. Gọi hàm process_doc()...")
            process_doc(file_path, output_path)
            print(f"✅ Word đã xử lý xong và lưu tại: {output_path}")

        elif ext in ['jpg', 'jpeg', 'png']:
            print("🖼️ Phát hiện ảnh. Gọi hàm process_image()...")
            image, results = process_image(file_path)
            for result in results:
                box, text, _ = result
                process_sensitive_info(image, box, text)
            cv2.imwrite(output_path, image)
            print(f"✅ Ảnh đã xử lý xong và lưu tại: {output_path}")

        else:
            raise ValueError(f"❌ Không hỗ trợ định dạng: {ext}")

    except Exception as e:
        logging.error(f"💥 Lỗi khi xử lý tệp {file_path}: {e}")
        print("❌ Lỗi chi tiết:")
        import traceback
        traceback.print_exc()
        raise

