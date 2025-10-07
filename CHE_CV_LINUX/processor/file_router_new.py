import os
import shutil
import urllib.request
import datetime
from processor.processor_new import process_file

def handle_file_by_url(file_id, url, root_folder):
    print("Tạo thư mục chứa CV")
    # Tạo thư mục ứng viên
    folder_uv = os.path.join(root_folder, f"uv_{file_id}")
    os.makedirs(folder_uv, exist_ok=True)

    print("Tải file CV")

    # Tải file về
    file_name = url.split("/")[-1]
    file_path = os.path.join(folder_uv, file_name)
    try:
        urllib.request.urlretrieve(url, file_path)
    except Exception as e:
        print("Không thể tải file từ URL")
        raise Exception(f"Không thể tải file từ URL: {url}. Lỗi: {e}")

    print("Bắt đầu xử lý file và tạo file")
    # Xử lý file và tạo file output
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    base_name = os.path.splitext(file_name)[0]
    output_filename = f"{base_name}_{timestamp}.png"
    output_path = os.path.join(folder_uv, output_filename)

    try:
        print("Đang xử lý file")
        process_file(file_path, output_path)
    except:
        print("Lỗi khi xử lý file ")

    # return output_path
    return output_path.replace("\\", "/")

