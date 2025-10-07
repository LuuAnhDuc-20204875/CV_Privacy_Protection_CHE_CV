from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import os, urllib.request, time, traceback
from processor.file_router import handle_file_by_url
from waitress import serve  # ✅ dùng waitress thay gunicorn

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/'

# ✅ Thread pool: xử lý song song tối đa 4 request
executor = ThreadPoolExecutor(max_workers=3)

def process_single_cv(item):
    file_id = item.get("id")
    url = item.get("link")
    try:
        start_time = time.time()
        print(f"🚀 Bắt đầu xử lý file {file_id}")
        output_link = handle_file_by_url(file_id, url, app.config['UPLOAD_FOLDER'])
        output_link = output_link.replace('static/', '')  # Đơn giản hóa đường dẫn nếu cần
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

    # ✅ Xử lý song song các item trong request
    results = list(executor.map(process_single_cv, data))
    return jsonify(results)

if __name__ == '__main__':
    print("🚀 API đang chạy bằng Waitress tại http://43.239.223.148:8000/hide_cv")
    serve(app, host='0.0.0.0', port=8000, threads=3)  # ✅ xử lý tối đa 4 request cùng lúc
