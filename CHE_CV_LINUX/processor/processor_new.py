import os
import cv2
import re
import numpy as np
import easyocr
import logging
import traceback
from pdf2image import convert_from_path  # Để xử lý PDF
from concurrent.futures import ThreadPoolExecutor, as_completed

# Tạo logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('log_processing.txt', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

reader = easyocr.Reader(['en', 'vi'])

def resize_if_large_viec3s(image, image_path=None, max_width=1400, save_preview=False):
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

def convert_doc_to_pdf_viec3s(doc_path, pdf_path):
    """Chuyển DOC/DOCX sang PDF trên Linux bằng LibreOffice"""
    try:
        abs_doc_path = os.path.abspath(doc_path)
        abs_pdf_path = os.path.abspath(pdf_path)

        print(f"📄 [Linux] Bắt đầu chuyển đổi DOC/DOCX sang PDF: {abs_doc_path}")
        # Gọi LibreOffice headless
        os.system(f'libreoffice --headless --convert-to pdf "{abs_doc_path}" --outdir "{os.path.dirname(abs_pdf_path)}"')

        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        auto_pdf = os.path.join(os.path.dirname(abs_pdf_path), f"{base_name}.pdf")
        if os.path.exists(auto_pdf):
            os.rename(auto_pdf, abs_pdf_path)
            print(f"✅ Đã chuyển thành PDF: {abs_pdf_path}")
            return abs_pdf_path
        else:
            print(f"❌ Không tìm thấy file PDF sau khi chuyển từ {abs_doc_path}")
            return None

    except Exception as e:
        print(f"❌ Lỗi chuyển đổi DOC/DOCX sang PDF trên Linux: {e}")
        logging.error(f"Lỗi chuyển đổi DOC sang PDF: {e}")
        traceback.print_exc()
        return None

def convert_pdf_to_image_viec3s(pdf_path, output_image_path):
    try:
        print(f"📄 Bắt đầu chuyển PDF sang ảnh: {pdf_path}")
        images = convert_from_path(pdf_path, 200)  # 200 DPI
        # images = convert_from_path(pdf_path, 300)  # 300 DPI
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


# def process_sensitive_info(image, box, text):
#     try:
#         text_lower = text.lower()
#         phone_pattern = r'(\+84|0)([.\-\s]?\d){8,10}'
#         email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?'
#         website_pattern = r'(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
#         specific_websites = r'(tuyendung3s\.com|viec3s\.com|timviec365\.vn)'
#         com_vn_pattern = r'(\.com|\.vn|\bcom\b|\bvn\b|timviec|tuyendung|viec3|vieclam|cuyendung|joblike|viecday|jobgo|topcv|job247|viechay|viecnhanh)'

#         if re.search(phone_pattern, text_lower) or \
#            re.search(email_pattern, text_lower) or \
#            re.search(website_pattern, text_lower) or \
#            re.search(specific_websites, text_lower) or \
#            re.search(com_vn_pattern, text_lower):

#             print(f"🔒 [MASK] Phát hiện thông tin nhạy cảm: {text}")
#             logging.info(f"Thông tin nhạy cảm: {text}")

#             x1, y1 = box[0]
#             x2, y2 = box[2]

#             region = image[int(y1):int(y2), int(x1):int(x2)]
#             colors, counts = np.unique(region.reshape(-1, 3), axis=0, return_counts=True)
#             dominant_color = colors[np.argmax(counts)]

#             # Tô màu nền của vùng chứa văn bản bằng màu chiếm ưu thế
#             image[int(y1):int(y2), int(x1):int(x2)] = dominant_color

#             # Vẽ bounding box quanh văn bản
#             # cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

#             # Hiển thị văn bản lên vùng đã được che giấu
#             # cv2.putText(image, text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            

#     except Exception as e:
#         print(f"❌ [MASK] Lỗi khi xử lý vùng nhạy cảm: {text}")
#         traceback.print_exc()



def process_sensitive_info_viec3s(image, box, text, mask_mode="all"):
    try:
        text_lower = text.lower()
        phone_pattern = r'(\+84|0)([.\-\s]?\d){8,10}'
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?'
        website_pattern = r'(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        specific_websites = r'(tuyendung3s\.com|viec3s\.com|timviec365\.vn|Timviec|timviec|timviec365|Timviec365)'
        com_vn_pattern = r'(\.com|\.vn|\bcom\b|\bvn\b|timviec|tuyendung|viec3|vieclam|cuyendung|joblike|viecday|jobgo|topcv|job247|viechay|viecnhanh)'
        watermark_pattern = r'\b(timviec|tuyendung|viec3|vieclam|cuyendung|joblike|viecday|jobgo|topcv|job247|viechay|viecnhanh)\b'


        is_phone = re.search(phone_pattern, text_lower)
        is_email = re.search(email_pattern, text_lower) or \
                    re.search(website_pattern, text_lower) or \
                    re.search(specific_websites, text_lower) or \
                    re.search(com_vn_pattern, text_lower)
        
        is_web = re.search(watermark_pattern, text_lower) or \
                    re.search(specific_websites, text_lower)

        if mask_mode == "all":
            should_mask = is_phone or is_email or is_web
        elif mask_mode == "watermark":
            should_mask = is_web
        else:
            should_mask = False

        if should_mask:
            print(f"🔒 [MASK-{mask_mode}] {text}")
            x1, y1 = box[0]
            x2, y2 = box[2]
            region = image[int(y1):int(y2), int(x1):int(x2)]
            colors, counts = np.unique(region.reshape(-1, 3), axis=0, return_counts=True)
            dominant_color = colors[np.argmax(counts)]
            
            
            # Tô màu nền của vùng chứa văn bản bằng màu chiếm ưu thế
            image[int(y1):int(y2), int(x1):int(x2)] = dominant_color

            # # Vẽ bounding box quanh văn bản
            # cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            # # Hiển thị văn bản lên vùng đã được che giấu
            # cv2.putText(image, text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)



    except Exception as e:
        print(f"❌ [MASK] Lỗi với {text}")
        traceback.print_exc()



def process_image_viec3s(image_path):
    print(f"📥 [IMG] Đang đọc ảnh: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        raise Exception(f"❌ Không đọc được ảnh từ file: {image_path}")
    print(f"✅ Ảnh đã được load: {image.shape}")
    image, preview_path = resize_if_large_viec3s(image, image_path, save_preview=True)
    print("🔎 Bắt đầu OCR...")
    results = reader.readtext(image)
    print(f"🔍 OCR phát hiện {len(results)} vùng văn bản.")
    return image, results


# def process_single_pdf_page(idx, image_path):
#     try:
#         print(f"🔄 [PDF] Đang xử lý trang {idx + 1}: {image_path}")
#         image = cv2.imread(image_path)
#         if image is None:
#             raise Exception(f"❌ Không đọc được ảnh từ file: {image_path}")

#         image, preview_path = resize_if_large(image, image_path, save_preview=True)
#         results = reader.readtext(image)
#         print(f"🔍 Trang {idx + 1}: {len(results)} vùng văn bản được phát hiện")
#         for result in results:
#             box, text, _ = result
#             process_sensitive_info(image, box, text)

#         return idx, image, preview_path
#     except Exception as e:
#         logging.error(f"❌ Lỗi xử lý trang {idx + 1} ({image_path}): {e}")
#         traceback.print_exc()
#         return idx, None, None  # vẫn trả idx để không vỡ thứ tự
    


def process_single_pdf_page_viec3s(idx, image_path, mask_mode="all"):
    try:
        print(f"🔄 [PDF] Đang xử lý trang {idx + 1}: {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise Exception(f"❌ Không đọc được ảnh từ file: {image_path}")

        image, preview_path = resize_if_large_viec3s(image, image_path, save_preview=True)
        results = reader.readtext(image)
        print(f"🔍 Trang {idx + 1}: {len(results)} vùng văn bản được phát hiện")
        for result in results:
            box, text, _ = result
            process_sensitive_info_viec3s(image, box, text, mask_mode)

        # ✅ Sau khi xử lý xong text, gọi che QR
        if mask_mode in ("all", "watermark"):
            detect_and_mask_qr_with_border_color_viec3s(image, ring=10, polygon=True, margin_fill=2)
            
        return idx, image, preview_path
    except Exception as e:
        logging.error(f"❌ Lỗi xử lý trang {idx + 1} ({image_path}): {e}")
        traceback.print_exc()
        return idx, None, None  # vẫn trả idx để không vỡ thứ tự




# def process_pdf(pdf_path, output_path):
#     print(f"\n🚀 [PDF] Bắt đầu xử lý PDF: {pdf_path}")
#     try:
#         images = convert_pdf_to_image(pdf_path, pdf_path)
#     except Exception as e:
#         print("❌ Lỗi quá trình xử lý PDF thành ảnh ....")
#         logging.error(f"Lỗi khi xử lý PDF: {e}")
#         traceback.print_exc()
#         return

#     max_workers = min(len(images), os.cpu_count() - 1 or 1)
#     print(f"⚙️ Sử dụng tối đa {max_workers} luồng để xử lý ảnh")

#     # tạo list kết quả bằng độ dài images
#     ordered_images = [None] * len(images)
#     preview_paths = [None] * len(images)

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         # submit kèm index
#         futures = [executor.submit(process_single_pdf_page, idx, image_path)
#                    for idx, image_path in enumerate(images)]
#         for future in futures:
#             idx, image, preview_path = future.result()
#             ordered_images[idx] = image
#             preview_paths[idx] = preview_path

#     try:
#         # lọc bỏ None
#         valid_images = [img for img in ordered_images if img is not None]
#         final_image = np.vstack(valid_images)
#         cv2.imwrite(output_path, final_image)
#         print(f"✅ Đã lưu kết quả sau khi xử lý PDF vào: {output_path}")
#     except Exception as e:
#         logging.error(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
#         print(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
#         traceback.print_exc()

#     # Xóa file tạm
#     for image_path in images:
#         if os.path.exists(image_path):
#             os.remove(image_path)
#             print(f"🧹 Đã xóa ảnh gốc: {image_path}")
#     for preview_path in preview_paths:
#         if preview_path and os.path.exists(preview_path):
#             os.remove(preview_path)
#             print(f"🧹 Đã xóa ảnh preview: {preview_path}")



def process_pdf_viec3s(pdf_path, output_path, mask_mode="all"):
    print(f"\n🚀 [PDF] Bắt đầu xử lý PDF: {pdf_path}")
    try:
        images = convert_pdf_to_image_viec3s(pdf_path, pdf_path)
    except Exception as e:
        print("❌ Lỗi quá trình xử lý PDF thành ảnh ....")
        logging.error(f"Lỗi khi xử lý PDF: {e}")
        traceback.print_exc()
        return

    max_workers = min(len(images), os.cpu_count() - 1 or 1)
    print(f"⚙️ Sử dụng tối đa {max_workers} luồng để xử lý ảnh")

    # tạo list kết quả bằng độ dài images
    ordered_images = [None] * len(images)
    preview_paths = [None] * len(images)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # submit kèm index
        futures = [executor.submit(process_single_pdf_page_viec3s, idx, image_path, mask_mode)
                for idx, image_path in enumerate(images)]
        for future in futures:
            idx, image, preview_path = future.result()
            ordered_images[idx] = image
            preview_paths[idx] = preview_path

    try:
        # lọc bỏ None
        valid_images = [img for img in ordered_images if img is not None]
        final_image = np.vstack(valid_images)
        cv2.imwrite(output_path, final_image)
        print(f"✅ Đã lưu kết quả sau khi xử lý PDF vào: {output_path}")
    except Exception as e:
        logging.error(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
        print(f"❌ Lỗi khi ghép hoặc lưu ảnh PDF: {e}")
        traceback.print_exc()

    # Xóa file tạm
    for image_path in images:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"🧹 Đã xóa ảnh gốc: {image_path}")
    for preview_path in preview_paths:
        if preview_path and os.path.exists(preview_path):
            os.remove(preview_path)
            print(f"🧹 Đã xóa ảnh preview: {preview_path}")



# def process_doc(doc_path, output_path):
#     print(f"\n📘 [WORD] Bắt đầu xử lý tệp Word: {doc_path}")
#     temp_pdf = os.path.join(os.path.dirname(output_path), 'temp.pdf')
#     converted_pdf = convert_doc_to_pdf(doc_path, temp_pdf)
#     if not converted_pdf or not os.path.exists(converted_pdf):
#         print("❌ Không thể chuyển Word sang PDF. Dừng xử lý.")
#         return
#     try:
#         process_pdf(converted_pdf, output_path)
#     except Exception as e:
#         print(f"❌ Lỗi xử lý PDF sau khi chuyển từ Word: {e}")
#         logging.error(f"Lỗi xử lý PDF từ Word: {e}")
#         traceback.print_exc()
#     if os.path.exists(temp_pdf):
#         os.remove(temp_pdf)
#         print("🧹 Đã xóa file tạm PDF sau xử lý.")


def process_doc_viec3s(doc_path, output_path, mask_mode="all"):
    print(f"\n📘 [WORD] Bắt đầu xử lý tệp Word: {doc_path}")
    temp_pdf = os.path.join(os.path.dirname(output_path), 'temp.pdf')
    converted_pdf = convert_doc_to_pdf_viec3s(doc_path, temp_pdf)
    if not converted_pdf or not os.path.exists(converted_pdf):
        print("❌ Không thể chuyển Word sang PDF. Dừng xử lý.")
        return
    try:
        process_pdf_viec3s(converted_pdf, output_path, mask_mode)
    except Exception as e:
        print(f"❌ Lỗi xử lý PDF sau khi chuyển từ Word: {e}")
        logging.error(f"Lỗi xử lý PDF từ Word: {e}")
        traceback.print_exc()
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
        print("🧹 Đã xóa file tạm PDF sau xử lý.")

# def process_file(file_path, output_path):
#     ext = file_path.split('.')[-1].lower()
#     print(f"\n📂 Đang xử lý file: {file_path}")
#     print(f"📄 Định dạng: {ext}")
#     try:
#         if ext == 'pdf':
#             process_pdf(file_path, output_path)
#             print(f"✅ PDF đã xử lý xong và lưu tại: {output_path}")
#         elif ext in ['doc', 'docx']:
#             process_doc(file_path, output_path)
#             print(f"✅ Word đã xử lý xong và lưu tại: {output_path}")
#         elif ext in ['jpg', 'jpeg', 'png']:
#             image, results = process_image(file_path)
#             for result in results:
#                 box, text, _ = result
#                 process_sensitive_info(image, box, text)
#             cv2.imwrite(output_path, image)
#             print(f"✅ Ảnh đã xử lý xong và lưu tại: {output_path}")
#         else:
#             raise ValueError(f"❌ Không hỗ trợ định dạng: {ext}")
#     except Exception as e:
#         logging.error(f"💥 Lỗi khi xử lý tệp {file_path}: {e}")
#         print("❌ Lỗi chi tiết:")
#         traceback.print_exc()
#         raise

# def detect_and_mask_qr_with_border_color_viec3s(image, ring=10, polygon=True, use_kmeans=False, margin_fill=2):
#     import cv2
#     import numpy as np

#     def _dominant_color_from_ring(image_bgr, ring_mask):
#         ring_pixels = image_bgr[ring_mask == 255]
#         if ring_pixels.size == 0:
#             return np.array([200, 200, 200], dtype=np.uint8)  # fallback
#         img_lab = cv2.cvtColor(ring_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3)
#         med_lab = np.median(img_lab, axis=0).astype(np.uint8)
#         bgr = cv2.cvtColor(med_lab.reshape(1, 1, 3), cv2.COLOR_LAB2BGR).reshape(3)
#         return bgr.astype(np.uint8)

#     h, w = image.shape[:2]
#     detector = cv2.QRCodeDetector()
#     points_list = []

#     try:
#         ok, _, pts_multi, _ = detector.detectAndDecodeMulti(image)
#         if ok and pts_multi is not None:
#             points_list = [p[0] if p.ndim == 3 else p for p in pts_multi]
#     except:
#         pass

#     if not points_list:
#         _, pts, _ = detector.detectAndDecode(image)
#         if pts is not None:
#             points_list = [pts[0] if pts.ndim == 3 else pts]

#     if not points_list:
#         return 0

#     mask_qr = np.zeros((h, w), dtype=np.uint8)
#     for pts in points_list:
#         pts = pts.astype(np.int32)
#         if polygon:
#             cv2.fillPoly(mask_qr, [pts], 255)
#         else:
#             x1, y1 = pts[:, 0].min(), pts[:, 1].min()
#             x2, y2 = pts[:, 0].max(), pts[:, 1].max()
#             cv2.rectangle(mask_qr, (x1, y1), (x2, y2), 255, thickness=-1)

#     k_ring = 2 * ring + 1
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_ring, k_ring))
#     mask_dilate = cv2.dilate(mask_qr, kernel)
#     ring_mask = cv2.subtract(mask_dilate, mask_qr)
#     dom_color = _dominant_color_from_ring(image, ring_mask)

#     mask_fill = mask_qr.copy()
#     if margin_fill > 0:
#         k_fill = 2 * margin_fill + 1
#         kernel_fill = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_fill, k_fill))
#         mask_fill = cv2.dilate(mask_fill, kernel_fill)

#     image[mask_fill == 255] = dom_color
#     return len(points_list)


# def detect_and_mask_qr_with_border_color_viec3s(image, ring=10, polygon=True, use_kmeans=False, margin_fill=2):
#     """
#     Phát hiện và che QR code trên ảnh, nhưng chỉ che khi vùng phát hiện
#     thực sự giống 1 hình vuông/hình chữ nhật gần như thẳng (không bị xoắn lệch).

#     Đồng thời log chi tiết những vùng được/có xem xét để dễ debug.
#     """

#     def _log(msg):
#         # Có thể thay bằng ghi_log_chi_tiet nếu anh đang dùng
#         try:
#             print(msg)
#         except Exception:
#             pass

#     def _dominant_color_from_ring(image_bgr, ring_mask):
#         ring_pixels = image_bgr[ring_mask == 255]
#         if ring_pixels.size == 0:
#             return np.array([200, 200, 200], dtype=np.uint8)  # fallback
#         img_lab = cv2.cvtColor(
#             ring_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB
#         ).reshape(-1, 3)
#         med_lab = np.median(img_lab, axis=0).astype(np.uint8)
#         bgr = cv2.cvtColor(med_lab.reshape(1, 1, 3), cv2.COLOR_LAB2BGR).reshape(3)
#         return bgr.astype(np.uint8)

#     def _order_points_axis_aligned(pts):
#         """Sắp xếp 4 điểm thành TL, TR, BR, BL theo trục ảnh (x ngang, y dọc)."""
#         pts = np.array(pts, dtype=np.float32).reshape(-1, 2)
#         if pts.shape[0] < 4:
#             return None

#         cx = np.mean(pts[:, 0])
#         cy = np.mean(pts[:, 1])

#         TL = TR = BR = BL = None
#         for (x, y) in pts:
#             if x <= cx and y <= cy:
#                 TL = (x, y)
#             elif x > cx and y <= cy:
#                 TR = (x, y)
#             elif x > cx and y > cy:
#                 BR = (x, y)
#             else:
#                 BL = (x, y)

#         if None in (TL, TR, BR, BL):
#             return None
#         return np.array([TL, TR, BR, BL], dtype=np.float32)

#     def _is_rect_like(pts, img_w, img_h,
#                       min_aspect=0.7, max_aspect=1.3,
#                       min_area_ratio=0.0005,
#                       max_tilt_ratio=0.2):
#         """Kiểm tra vùng pts có giống hình vuông/chữ nhật hay không.

#         Điều kiện:
#         - Tỉ lệ cạnh bbox: aspect = max(w, h) / min(w, h) trong [min_aspect, max_aspect]
#         - Diện tích bbox đủ lớn (area_ratio >= min_area_ratio)
#         - 4 góc sau khi sắp xếp TL, TR, BR, BL gần song song với trục ảnh:
#             + |y_TL - y_TR| và |y_BL - y_BR| nhỏ hơn max_tilt_ratio * chiều cao bbox
#             + |x_TL - x_BL| và |x_TR - x_BR| nhỏ hơn max_tilt_ratio * chiều rộng bbox
#         """
#         pts = np.array(pts, dtype=np.float32).reshape(-1, 2)
#         if pts.shape[0] < 4:
#             _log(f"[QR-CHECK] Bỏ qua vì số điểm < 4: pts.shape={pts.shape}")
#             return False

#         pts_int = pts.astype(np.int32)
#         x1, y1 = pts_int[:, 0].min(), pts_int[:, 1].min()
#         x2, y2 = pts_int[:, 0].max(), pts_int[:, 1].max()
#         w_box = x2 - x1
#         h_box = y2 - y1
#         if w_box <= 0 or h_box <= 0:
#             _log(f"[QR-CHECK] Bỏ qua vì bbox không hợp lệ w={w_box}, h={h_box}")
#             return False

#         aspect = max(w_box, h_box) / float(min(w_box, h_box))
#         area = w_box * h_box
#         img_area = img_w * img_h
#         area_ratio = area / float(img_area)

#         if not (min_aspect <= aspect <= max_aspect):
#             _log(f"[QR-CHECK] Reject vì aspect={aspect:.3f} ngoài [{min_aspect}, {max_aspect}]")
#             return False
#         if area_ratio < min_area_ratio:
#             _log(f"[QR-CHECK] Reject vì area_ratio={area_ratio:.6f} < {min_area_ratio}")
#             return False

#         ordered = _order_points_axis_aligned(pts)
#         if ordered is None:
#             _log("[QR-CHECK] Reject vì không sắp xếp được TL,TR,BR,BL")
#             return False

#         TL, TR, BR, BL = ordered

#         top_y_diff = abs(TL[1] - TR[1])
#         bottom_y_diff = abs(BL[1] - BR[1])
#         left_x_diff = abs(TL[0] - BL[0])
#         right_x_diff = abs(TR[0] - BR[0])

#         max_y_diff = max_tilt_ratio * h_box
#         max_x_diff = max_tilt_ratio * w_box

#         if (top_y_diff > max_y_diff or bottom_y_diff > max_y_diff or
#                 left_x_diff > max_x_diff or right_x_diff > max_x_diff):
#             _log(
#                 f"[QR-CHECK] Reject vì lệch trục: "
#                 f"top_y_diff={top_y_diff:.2f}, bottom_y_diff={bottom_y_diff:.2f}, "
#                 f"left_x_diff={left_x_diff:.2f}, right_x_diff={right_x_diff:.2f}, "
#                 f"ngưỡng_y<={max_y_diff:.2f}, ngưỡng_x<={max_x_diff:.2f}"
#             )
#             return False

#         _log(
#             f"[QR-CHECK] ACCEPT bbox=({x1},{y1},{x2},{y2}), aspect={aspect:.3f}, "
#             f"area_ratio={area_ratio:.6f}, pts={ordered.tolist()}"
#         )
#         return True

#     h, w = image.shape[:2]
#     detector = cv2.QRCodeDetector()
#     raw_points_list = []

#     # 1. Thử detect nhiều QR
#     try:
#         ok, _, pts_multi, _ = detector.detectAndDecodeMulti(image)
#         if ok and pts_multi is not None:
#             for p in pts_multi:
#                 pts = p[0] if p.ndim == 3 else p
#                 raw_points_list.append(pts)
#     except Exception as e:
#         _log(f"[QR] detectAndDecodeMulti error: {e}")

#     # 2. Nếu không có, fallback về detect đơn
#     if not raw_points_list:
#         try:
#             _, pts, _ = detector.detectAndDecode(image)
#             if pts is not None:
#                 pts = pts[0] if pts.ndim == 3 else pts
#                 raw_points_list.append(pts)
#         except Exception as e:
#             _log(f"[QR] detectAndDecode error: {e}")

#     if not raw_points_list:
#         _log("[QR] Không phát hiện được vùng nào nghi là QR")
#         return 0

#     # 3. Lọc lại chỉ giữ vùng nào có dạng hình vuông/chữ nhật hợp lệ
#     points_list = []
#     for idx, pts in enumerate(raw_points_list):
#         if _is_rect_like(pts, w, h):
#             points_list.append(np.array(pts, dtype=np.float32))
#         else:
#             _log(f"[QR] Vùng #{idx} bị loại, không giống QR đủ điều kiện")

#     # Nếu sau khi lọc không còn vùng nào “đáng tin” → không che gì cả
#     if not points_list:
#         _log("[QR] Không có vùng nào qua được filter hình vuông/hcn, không che gì")
#         return 0

#     # 4. Tạo mask QR
#     mask_qr = np.zeros((h, w), dtype=np.uint8)
#     for pts in points_list:
#         pts_int = pts.astype(np.int32)
#         if polygon:
#             cv2.fillPoly(mask_qr, [pts_int], 255)
#         else:
#             x1, y1 = pts_int[:, 0].min(), pts_int[:, 1].min()
#             x2, y2 = pts_int[:, 0].max(), pts_int[:, 1].max()
#             cv2.rectangle(mask_qr, (x1, y1), (x2, y2), 255, thickness=-1)

#     # 5. Tạo ring quanh QR để lấy màu nền
#     k_ring = 2 * ring + 1
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_ring, k_ring))
#     mask_dilate = cv2.dilate(mask_qr, kernel)
#     ring_mask = cv2.subtract(mask_dilate, mask_qr)
#     dom_color = _dominant_color_from_ring(image, ring_mask)

#     # 6. Mở rộng vùng che (margin_fill)
#     mask_fill = mask_qr.copy()
#     if margin_fill > 0:
#         k_fill = 2 * margin_fill + 1
#         kernel_fill = cv2.getStructuringElement(
#             cv2.MORPH_ELLIPSE, (k_fill, k_fill)
#         )
#         mask_fill = cv2.dilate(mask_fill, kernel_fill)

#     # 7. Che QR bằng màu nền
#     image[mask_fill == 255] = dom_color

#     _log(f"[QR] Đã che {len(points_list)} vùng nghi là QR")
#     return len(points_list)

def detect_and_mask_qr_with_border_color_viec3s(image, ring=10, polygon=True, use_kmeans=False, margin_fill=2):
    """Phát hiện và che QR code trên CV.

    Ưu tiên:
    - Dùng QRCodeDetector (ảnh gốc + chia đôi + resize) để tìm ứng viên.
    - Chỉ giữ vùng thật sự gần hình vuông/chữ nhật thẳng trục.
    - Nếu vẫn không có gì, dùng fallback tìm ô vuông ở đáy CV (QR thường nằm cuối CV bên phải).
    - Log chi tiết để dễ debug.
    """
    import cv2
    import numpy as np

    def _log(msg):
        try:
            print(msg)
        except Exception:
            pass

    # ----------------- Lấy màu nền quanh QR -----------------
    def _dominant_color_from_ring(image_bgr, ring_mask):
        ring_pixels = image_bgr[ring_mask == 255]
        if ring_pixels.size == 0:
            return np.array([200, 200, 200], dtype=np.uint8)  # fallback
        img_lab = cv2.cvtColor(
            ring_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB
        ).reshape(-1, 3)
        med_lab = np.median(img_lab, axis=0).astype(np.uint8)
        bgr = cv2.cvtColor(med_lab.reshape(1, 1, 3), cv2.COLOR_LAB2BGR).reshape(3)
        return bgr.astype(np.uint8)

    # ----------------- Sắp xếp 4 điểm TL,TR,BR,BL -----------------
    def _order_points_axis_aligned(pts):
        pts = np.array(pts, dtype=np.float32).reshape(-1, 2)
        if pts.shape[0] < 4:
            return None

        cx = np.mean(pts[:, 0])
        cy = np.mean(pts[:, 1])

        TL = TR = BR = BL = None
        for (x, y) in pts:
            if x <= cx and y <= cy:
                TL = (x, y)
            elif x > cx and y <= cy:
                TR = (x, y)
            elif x > cx and y > cy:
                BR = (x, y)
            else:
                BL = (x, y)

        if None in (TL, TR, BR, BL):
            return None
        return np.array([TL, TR, BR, BL], dtype=np.float32)

    # ----------------- Check hình vuông/chữ nhật thẳng -----------------
    def _is_rect_like(pts, img_w, img_h,
                      min_aspect=0.7, max_aspect=1.3,
                      min_area_ratio=0.0001,
                      max_tilt_ratio=0.25):
        pts = np.array(pts, dtype=np.float32).reshape(-1, 2)
        if pts.shape[0] < 4:
            _log(f"[QR-CHECK] Bỏ qua vì số điểm < 4: pts.shape={pts.shape}")
            return False

        pts_int = pts.astype(np.int32)
        x1, y1 = pts_int[:, 0].min(), pts_int[:, 1].min()
        x2, y2 = pts_int[:, 0].max(), pts_int[:, 1].max()
        w_box = x2 - x1
        h_box = y2 - y1
        if w_box <= 0 or h_box <= 0:
            _log(f"[QR-CHECK] Bỏ qua vì bbox không hợp lệ w={w_box}, h={h_box}")
            return False

        aspect = max(w_box, h_box) / float(min(w_box, h_box))
        area = w_box * h_box
        img_area = img_w * img_h
        area_ratio = area / float(img_area)

        if not (min_aspect <= aspect <= max_aspect):
            _log(f"[QR-CHECK] Reject vì aspect={aspect:.3f} ngoài [{min_aspect}, {max_aspect}]")
            return False
        if area_ratio < min_area_ratio:
            _log(f"[QR-CHECK] Reject vì area_ratio={area_ratio:.6f} < {min_area_ratio}")
            return False

        ordered = _order_points_axis_aligned(pts)
        if ordered is None:
            _log("[QR-CHECK] Reject vì không sắp xếp được TL,TR,BR,BL")
            return False

        TL, TR, BR, BL = ordered

        top_y_diff = abs(TL[1] - TR[1])
        bottom_y_diff = abs(BL[1] - BR[1])
        left_x_diff = abs(TL[0] - BL[0])
        right_x_diff = abs(TR[0] - BR[0])

        max_y_diff = max_tilt_ratio * h_box
        max_x_diff = max_tilt_ratio * w_box

        if (top_y_diff > max_y_diff or bottom_y_diff > max_y_diff or
                left_x_diff > max_x_diff or right_x_diff > max_x_diff):
            _log(
                f"[QR-CHECK] Reject vì lệch trục: "
                f"top_y_diff={top_y_diff:.2f}, bottom_y_diff={bottom_y_diff:.2f}, "
                f"left_x_diff={left_x_diff:.2f}, right_x_diff={right_x_diff:.2f}, "
                f"ngưỡng_y<={max_y_diff:.2f}, ngưỡng_x<={max_x_diff:.2f}"
            )
            return False

        _log(
            f"[QR-CHECK] ACCEPT bbox=({x1},{y1},{x2},{y2}), aspect={aspect:.3f}, "
            f"area_ratio={area_ratio:.6f}, pts={ordered.tolist()}"
        )
        return True

    # ----------------- Detect QR trên 1 ROI bằng QRCodeDetector -----------------
    detector = cv2.QRCodeDetector()

    def _detect_candidates_on_roi(img_roi, x_offset=0, y_offset=0):
        h_r, w_r = img_roi.shape[:2]
        raw = []

        max_side = max(h_r, w_r)
        scale = max_side / 1200.0  # đưa cạnh dài về ~1200px
        if scale > 1.0:
            new_w = int(w_r / scale)
            new_h = int(h_r / scale)
            small = cv2.resize(img_roi, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            small = img_roi.copy()
            scale = 1.0

        _log(f"[QR] Detect ROI size=({w_r},{h_r}), resized_scale={scale:.3f}, offset=({x_offset},{y_offset})")

        try:
            ok_s, _, pts_multi_s, _ = detector.detectAndDecodeMulti(small)
            if ok_s and pts_multi_s is not None:
                for p in pts_multi_s:
                    pts_s = p[0] if p.ndim == 3 else p
                    pts_orig = pts_s.astype(np.float32)
                    pts_orig[:, 0] *= scale
                    pts_orig[:, 1] *= scale
                    pts_orig[:, 0] += x_offset
                    pts_orig[:, 1] += y_offset
                    raw.append(pts_orig)
        except Exception as e:
            _log(f"[QR] detectAndDecodeMulti ROI error: {e}")

        if not raw:
            try:
                _, pts_s, _ = detector.detectAndDecode(small)
                if pts_s is not None:
                    pts_s = pts_s[0] if pts_s.ndim == 3 else pts_s
                    pts_orig = pts_s.astype(np.float32)
                    pts_orig[:, 0] *= scale
                    pts_orig[:, 1] *= scale
                    pts_orig[:, 0] += x_offset
                    pts_orig[:, 1] += y_offset
                    raw.append(pts_orig)
            except Exception as e:
                _log(f"[QR] detectAndDecode ROI error: {e}")

        return raw

    # ----------------- Fallback: tìm ô vuông ở đáy CV -----------------
    def _find_qr_bottom_square(img, bottom_ratio=0.7):
        h0, w0 = img.shape[:2]
        y0 = int(h0 * bottom_ratio)
        roi = img[y0:h0, :]
        roi_h, roi_w = roi.shape[:2]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        roi_area = roi_w * roi_h

        candidates = []
        for cnt in contours:
            x, y, w_box, h_box = cv2.boundingRect(cnt)
            area = w_box * h_box
            if area < 0.0005 * roi_area or area > 0.1 * roi_area:
                continue
            aspect = max(w_box, h_box) / float(min(w_box, h_box)) if min(w_box, h_box) > 0 else 999
            if not (0.8 <= aspect <= 1.2):
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.05 * peri, True)
            if len(approx) < 4 or len(approx) > 8:
                continue

            cx = x + w_box / 2
            cy = y + h_box / 2
            # Ưu tiên góc phải – phía dưới của ROI
            if cx < 0.7 * roi_w or cy < 0.3 * roi_h:
                continue

            pts = np.array([
                [x, y],
                [x + w_box, y],
                [x + w_box, y + h_box],
                [x, y + h_box]
            ], dtype=np.float32)
            pts[:, 1] += y0  # map lên toạ độ full ảnh
            candidates.append((area, pts))

        candidates.sort(key=lambda t: -t[0])
        if candidates:
            _log(f"[QR-FALLBACK] Tìm được {len(candidates)} ô vuông ở đáy CV, chọn ô lớn nhất area={candidates[0][0]}")
        else:
            _log("[QR-FALLBACK] Không tìm được ô vuông phù hợp ở đáy CV")

        return [pts for area, pts in candidates]

    # ----------------- Bắt đầu xử lý -----------------
    h, w = image.shape[:2]
    raw_points_list = []

    # 1) Detect trên toàn ảnh
    raw_points_list.extend(_detect_candidates_on_roi(image, 0, 0))

    # 2) Ảnh dọc/ảnh rất dài → detect thêm trên nửa trên & nửa dưới
    if h > 2000 or h > 1.6 * w:
        mid = h // 2
        _log("[QR] Ảnh dài, detect thêm trên nửa trên & nửa dưới")
        top_roi = image[0:mid, :]
        bot_roi = image[mid:h, :]
        raw_points_list.extend(_detect_candidates_on_roi(top_roi, 0, 0))
        raw_points_list.extend(_detect_candidates_on_roi(bot_roi, 0, mid))

    # 3) Lọc vùng giống hình vuông/hình chữ nhật
    points_list = []
    for idx, pts in enumerate(raw_points_list):
        if _is_rect_like(pts, w, h):
            points_list.append(np.array(pts, dtype=np.float32))
        else:
            _log(f"[QR] Vùng #{idx} bị loại, không giống QR đủ điều kiện")

    # 4) Không có gì → dùng fallback đáy CV
    if not points_list:
        _log("[QR] Không có vùng nào qua filter QRCodeDetector, dùng fallback đáy CV")
        bottom_pts_list = _find_qr_bottom_square(image, bottom_ratio=0.7)
        for pts in bottom_pts_list:
            if _is_rect_like(pts, w, h):
                points_list.append(np.array(pts, dtype=np.float32))

    if not points_list:
        _log("[QR] Cuối cùng vẫn không tìm được vùng nào đáng tin là QR, không che gì")
        return 0

    # 5) Tạo mask QR
    mask_qr = np.zeros((h, w), dtype=np.uint8)
    for pts in points_list:
        pts_int = pts.astype(np.int32)
        if polygon:
            cv2.fillPoly(mask_qr, [pts_int], 255)
        else:
            x1, y1 = pts_int[:, 0].min(), pts_int[:, 1].min()
            x2, y2 = pts_int[:, 0].max(), pts_int[:, 1].max()
            cv2.rectangle(mask_qr, (x1, y1), (x2, y2), 255, thickness=-1)

    # 6) Tạo ring quanh QR để lấy màu nền
    k_ring = 2 * ring + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_ring, k_ring))
    mask_dilate = cv2.dilate(mask_qr, kernel)
    ring_mask = cv2.subtract(mask_dilate, mask_qr)
    dom_color = _dominant_color_from_ring(image, ring_mask)

    # 7) Mở rộng vùng che (margin_fill)
    mask_fill = mask_qr.copy()
    if margin_fill > 0:
        k_fill = 2 * margin_fill + 1
        kernel_fill = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (k_fill, k_fill)
        )
        mask_fill = cv2.dilate(mask_fill, kernel_fill)

    # 8) Che QR bằng màu nền
    image[mask_fill == 255] = dom_color

    _log(f"[QR] Đã che {len(points_list)} vùng nghi là QR")
    return len(points_list)




def process_file_viec3s(file_path, output_path_all, output_path_watermark):
    ext = file_path.split('.')[-1].lower()
    print(f"\n📂 Đang xử lý file: {file_path}")
    print(f"📄 Định dạng: {ext}")

    try:
        if ext == 'pdf':
            from pdf2image import convert_from_path
            images = convert_from_path(file_path, 200)
            list_all = []
            list_watermark = []

            for idx, image_pil in enumerate(images):
                print(f"🖼️ Trang {idx + 1}")
                image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
                image, _ = resize_if_large_viec3s(image)

                results = reader.readtext(image)

                image_all = image.copy()
                image_watermark = image.copy()

                for box, text, _ in results:
                    process_sensitive_info_viec3s(image_all, box, text, mask_mode="all")
                    process_sensitive_info_viec3s(image_watermark, box, text, mask_mode="watermark")

                # ✅ Sau vòng for, thêm che QR cho từng ảnh
                detect_and_mask_qr_with_border_color_viec3s(image_all, ring=10, polygon=True, margin_fill=2)
                detect_and_mask_qr_with_border_color_viec3s(image_watermark, ring=10, polygon=True, margin_fill=2)


                list_all.append(image_all)
                list_watermark.append(image_watermark)

            # Ghép dọc các ảnh
            final_all = np.vstack(list_all)
            final_watermark = np.vstack(list_watermark)

            cv2.imwrite(output_path_all, final_all)
            cv2.imwrite(output_path_watermark, final_watermark)

        elif ext in ['jpg', 'jpeg', 'png']:
            image = cv2.imread(file_path)
            image, _ = resize_if_large_viec3s(image)
            results = reader.readtext(image)

            image_all = image.copy()
            image_watermark = image.copy()

            for box, text, _ in results:
                process_sensitive_info_viec3s(image_all, box, text, mask_mode="all")
                process_sensitive_info_viec3s(image_watermark, box, text, mask_mode="watermark")

            # ✅ Sau vòng for, thêm che QR cho từng ảnh
            detect_and_mask_qr_with_border_color_viec3s(image_all, ring=10, polygon=True, margin_fill=2)
            detect_and_mask_qr_with_border_color_viec3s(image_watermark, ring=10, polygon=True, margin_fill=2)

            cv2.imwrite(output_path_all, image_all)
            cv2.imwrite(output_path_watermark, image_watermark)

        elif ext in ['doc', 'docx']:
            print("📘 File Word phát hiện → Chuyển sang PDF và xử lý...")
            # Dùng hàm có sẵn + gọi lại chính process_file_viec3s
            process_doc_viec3s(file_path, output_path_all, mask_mode="all")
            process_doc_viec3s(file_path, output_path_watermark, mask_mode="watermark")
            
        else:
            raise ValueError("❌ Không hỗ trợ định dạng: " + ext)

    except Exception as e:
        print("❌ Lỗi khi xử lý file:")
        traceback.print_exc()
        raise
