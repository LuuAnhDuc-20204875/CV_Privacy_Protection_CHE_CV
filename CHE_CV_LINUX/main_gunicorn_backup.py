from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import os, urllib.request, time
from processor.file_router_new import handle_file_by_url
import traceback
import multiprocessing

# Khởi tạo Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'PaddleOCR/static/'

# Tạo executor với số luồng bằng số core - 1 (giữ lại 1 core cho hệ thống)
max_workers = 3
print(f"Số core sử dụng: {max_workers}")
executor = ThreadPoolExecutor(max_workers=max_workers)

def process_single_cv(item):
    file_id = item.get("id")
    url = item.get("link")
    try:
        start_time = time.time()
        print(f"🚀 Bắt đầu xử lý file {file_id}")
        output_link = handle_file_by_url(file_id, url, app.config['UPLOAD_FOLDER'])
        output_link = output_link.replace('PaddleOCR/', '')  # chuẩn hóa đường dẫn
        end_time = time.time()
        print(f"✅ Xử lý xong file {file_id} trong {end_time - start_time:.2f} giây")
        return {
            "id": file_id,
            "link": output_link,
            "link_error": 0
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "id": file_id,
            "link": "",
            "link_error": 1
        }

@app.route('/hide_cv', methods=['POST'])
def hide_cv():
    print("📥 API /hide_cv đã được gọi")
    data = request.json
    print(f"➡️ Tổng số file cần xử lý: {len(data)}")

    results = list(executor.map(process_single_cv, data))

    return jsonify(results)

# ⚠️ KHÔNG cần đoạn này khi chạy bằng gunicorn
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8000, debug=False)
