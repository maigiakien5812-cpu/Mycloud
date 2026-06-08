from flask import Flask, request, send_from_directory, redirect, jsonify, Response
import os
import re

app = Flask(__name__)

# Thư mục lưu trữ trực tiếp trên server Render
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():
    files = os.listdir(UPLOAD_FOLDER)

    html = """
    <html>
    <head>
    <title>⚡ My Cloud Tạm Thời Pro ⚡</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: #0f172a; color: white; font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; margin: 0; }
        .container { max-width: 600px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #38bdf8; margin-top: 10px; }
        button { background: #2563eb; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.2s; width: 100%; }
        button:hover { background: #1d4ed8; }
        button:disabled { background: #475569; cursor: not-allowed; }
        input[type="file"] { width: 100%; padding: 10px; background: #334155; border-radius: 8px; color: #cbd5e1; border: 1px dashed #475569; box-sizing: border-box; }
        a { color: #38bdf8; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        
        progress { width: 100%; height: 20px; border-radius: 10px; margin-top: 15px; display: block; overflow: hidden; }
        progress::-webkit-progress-bar { background-color: #334155; }
        progress::-webkit-progress-value { background-color: #0284c7; transition: width 0.1s ease; }
        
        .file-item { border-bottom: 1px solid #334155; padding: 15px 0; }
        .file-item:last-child { border-bottom: none; }
        .status-text { margin-top: 8px; font-size: 14px; font-weight: 500; }
        
        .preview-img { 
            max-width: 100%; 
            max-height: 250px; 
            border-radius: 10px; 
            margin-top: 12px; 
            display: block; 
            border: 1px solid #334155;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .preview-video {
            width: 100%;
            max-height: 300px;
            border-radius: 10px;
            margin-top: 12px;
            display: block;
            background: #000;
            border: 1px solid #334155;
        }
    </style>
    </head>
    <body>
    <div class="container">
        <h1>☁ My Cloud Pro (Local)</h1>
        
        <div class="card">
            <input type="file" id="fileInput">
            <br><br>
            <button id="uploadBtn" onclick="startUpload()">Bắt đầu tải lên 🚀</button>
            
            <div id="progressContainer" style="display: none;">
                <progress id="progressBar" value="0" max="100"></progress>
                <div class="status-text">
                    <span id="progressText" style="color: #38bdf8;">0%</span> - 
                    <span id="status" style="color: #94a3b8;">Đang chuẩn bị...</span>
                </div>
            </div>
        </div>

        <div class="card">
            <h3 style="margin-top:0; border-bottom: 2px solid #38bdf8; padding-bottom: 8px;">📁 File Đang Lưu Trữ</h3>
    """

    if not files:
        html += "<p style='color:#64748b; text-align:center;'>Chưa có file nào trên server ní ơi 🗿</p>"

    for f in files:
        path = os.path.join(UPLOAD_FOLDER, f)
        try:
            size = round(os.path.getsize(path) / (1024 * 1024), 2)
            size_str = f"{size} MB" if size >= 0.1 else f"{round(os.path.getsize(path)/1024, 2)} KB"
        except:
            size_str = "Không rõ"

        view_link = f"/view/{f}"
        html += f"""
        <div class="file-item">
            <b style="word-break: break-all; color: #f1f5f9;">{f}</b> <span style="color:#94a3b8; font-size:12px;">({size_str})</span>
            <br><br>
            <a href="/download/{f}">⬇ Tải về</a> | 
            <a href="/delete/{f}" style="color: #f87171;" onclick="return confirm('Xóa file này nha ní?')">🗑 Xóa</a>
        """

        f_lower = f.lower()
        if f_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            html += f'<br><img class="preview-img" src="{view_link}">'
            
        elif f_lower.endswith((".mp4", ".webm", ".ogg", ".mov")):
            # Thêm playsinline để chạy mượt trên cả trình duyệt điện thoại
            html += f'<br><video class="preview-video" src="{view_link}" controls preload="metadata" playsinline></video>'

        html += "</div>"

    html += """
        </div>
    </div>

    <script>
    const CHUNK_SIZE = 1024 * 1024; 
    const MAX_RETRIES = 5;          

    function startUpload() {
        let fileInput = document.getElementById("fileInput");
        let file = fileInput.files[0];

        if (!file) {
            alert("Ní chưa chọn file kìa! 🗿");
            return;
        }

        document.getElementById("uploadBtn").disabled = true;
        fileInput.disabled = true;
        
        document.getElementById("progressContainer").style.display = "block";
        document.getElementById("progressBar").value = 0;
        document.getElementById("progressText").innerText = "0%";
        document.getElementById("status").innerText = "Đang kết nối...";

        uploadChunk(file, 0, 0);
    }

    function uploadChunk(file, start, retries) {
        let end = Math.min(start + CHUNK_SIZE, file.size);
        let chunk = file.slice(start, end);

        let formData = new FormData();
        formData.append("file", chunk, file.name);
        formData.append("filename", file.name);
        formData.append("offset", start);

        let xhr = new XMLHttpRequest();
        xhr.timeout = 25000; 

        xhr.upload.addEventListener("progress", function(e) {
            if (e.lengthComputable) {
                let totalUploaded = start + e.loaded;
                let percent = Math.round((totalUploaded / file.size) * 100);
                if (percent >= 100) percent = 99; 

                document.getElementById("progressBar").value = percent;
                document.getElementById("progressText").innerText = percent + "%";
                document.getElementById("status").innerText = `Đang tải lên... (${Math.round(end/(1024*1024))}/${Math.round(file.size/(1024*1024))} MB)`;
                document.getElementById("status").style.color = "#38bdf8";
            }
        });

        xhr.onload = function() {
            if (xhr.status == 200) {
                if (end < file.size) {
                    uploadChunk(file, end, 0);
                } else {
                    document.getElementById("progressBar").value = 100;
                    document.getElementById("progressText").innerText = "100%";
                    document.getElementById("status").innerText = "Hoàn thành! Đang làm mới trang...";
                    document.getElementById("status").style.color = "#4ade80"; 
                    setTimeout(() => { location.reload(); }, 1500);
                }
            } else {
                handleRetry(file, start, retries, "Lỗi server (" + xhr.status + ")");
            }
        };

        xhr.onerror = function() { handleRetry(file, start, retries, "Mạng chập chờn"); };
        xhr.ontimeout = function() { handleRetry(file, start, retries, "Hết thời gian chờ"); };

        xhr.open("POST", "/upload");
        xhr.send(formData);
    }

    function handleRetry(file, start, retries, reason) {
        if (retries < MAX_RETRIES) {
            let nextRetry = retries + 1;
            document.getElementById("status").innerText = `⚠️ ${reason}. Đang thử lại lần ${nextRetry}/${MAX_RETRIES}...`;
            document.getElementById("status").style.color = "#f59e0b";
            setTimeout(() => { uploadChunk(file, start, nextRetry); }, 2000);
        } else {
            document.getElementById("status").innerText = "❌ Thất bại liên tiếp. Kiểm tra lại mạng nha!";
            document.getElementById("status").style.color = "#f87171";
            document.getElementById("uploadBtn").disabled = false;
            document.getElementById("fileInput").disabled = false;
        }
    }
    </script>
    </body>
    </html>
    """
    return html


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get("file")
        filename = request.form.get("filename")
        offset = int(request.form.get("offset", 0))

        if not file or not filename:
            return jsonify({"status": "error", "message": "Dữ liệu trống"}), 400

        path = os.path.join(UPLOAD_FOLDER, filename)

        if offset == 0:
            mode = "wb"
        else:
            if not os.path.exists(path):
                mode = "wb"
                offset = 0
            else:
                mode = "r+b"

        with open(path, mode) as f:
            if mode == "r+b":
                f.seek(offset)
            f.write(file.read())

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# CẬP NHẬT: Route xem file thông minh hỗ trợ Range Requests để xem video mượt mà
@app.route("/view/<filename>")
def view(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(path):
        return "File không tồn tại", 404

    # Nếu không phải video, gửi file như bình thường
    if not filename.lower().endswith((".mp4", ".webm", ".ogg", ".mov")):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Xử lý Range Header cho Video phát trên điện thoại
    file_size = os.path.getsize(path)
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        return send_from_directory(UPLOAD_FOLDER, filename)

    byte1, byte2 = None, None
    match = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if match:
        byte1 = match.group(1)
        byte2 = match.group(2)

    start = int(byte1) if byte1 else 0
    end = int(byte2) if byte2 else file_size - 1
    if end >= file_size:
        end = file_size - 1
    
    length = end - start + 1

    def generate():
        with open(path, 'rb') as f:
            f.seek(start)
            chunk_size = 1024 * 1024  # Đọc từng block 1MB gửi đi
            bytes_left = length
            while bytes_left > 0:
                to_read = min(chunk_size, bytes_left)
                data = f.read(to_read)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    # Trả về mã lỗi 206 (Partial Content) đúng chuẩn streaming video
    resp = Response(generate(), 206, mimetype='video/mp4', content_type='video/mp4', direct_passthrough=True)
    resp.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    resp.headers.add('Accept-Ranges', 'bytes')
    resp.headers.add('Content-Length', str(length))
    return resp


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/delete/<filename>")
def delete(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
        
