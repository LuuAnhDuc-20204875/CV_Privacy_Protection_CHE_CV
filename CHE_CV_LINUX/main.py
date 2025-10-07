from flask import Flask, request, jsonify
import os, urllib.request, time
from processor.file_router import handle_file_by_url
import traceback


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'PaddleOCR/static/'

@app.route('/hide_cv', methods=['POST'])
def hide_cv():
    print("📥 API /hide_cv đã được gọi")
    print("➡️ Dữ liệu nhận được:", request.data)

    data = request.json
    result = []

    for item in data:
        file_id = item.get("id")
        url = item.get("link")

        try:
            start_time = time.time()
            try:
                print("Bắt đầu xử lý file")
                output_link = handle_file_by_url(file_id, url, app.config['UPLOAD_FOLDER'])
                    # Loại bỏ phần PaddleOCR nếu có trong output_link
                output_link = output_link.replace('PaddleOCR/', '')
            except:
                print("Lỗi khi xử lý file")
            end_time = time.time()
            print(f"Tổng thời gian xử lý ảnh: {end_time - start_time:.2f} giây")

            result.append({
                "id": file_id,
                "link": output_link,
                "link_error": 0
            })

        except Exception as e:
            traceback.print_exc()
            result.append({
                "id": file_id,
                "link": "",
                "link_error": 1
            })


    return jsonify(result)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)
