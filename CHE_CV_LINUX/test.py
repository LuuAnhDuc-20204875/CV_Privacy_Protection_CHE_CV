import easyocr
import cv2
import traceback

image_path = 'static/uv_5781240/cv_17586401040_1111785022.pdf_page_1.jpg'

img = cv2.imread(image_path)
if img is None:
    print(f"❌ Không đọc được ảnh: {image_path}")
else:
    print(f"✅ Ảnh đã được load: {img.shape}")

    # Resize nếu ảnh quá to
    if img.shape[1] > 1200:
        scale = 1200 / img.shape[1]
        img = cv2.resize(img, None, fx=scale, fy=scale)
        print(f"🔧 Đã resize ảnh xuống còn: {img.shape}")

        # ✅ Lưu lại ảnh đã resize để xem
        output_preview_path = "static/resized_preview.jpg"
        cv2.imwrite(output_preview_path, img)
        print(f"💾 Ảnh resize đã lưu tại: {output_preview_path}")

    try:
        reader = easyocr.Reader(['en', 'vi'], verbose=True)
        print("🔎 Bắt đầu OCR...")
        results = reader.readtext(img)
        print(f"✅ Đã đọc được {len(results)} đoạn văn bản:")
        for box, text, conf in results:
            print(f"{text} (conf: {conf:.2f})")
    except Exception as e:
        print("❌ Lỗi khi chạy OCR:")
        traceback.print_exc()
