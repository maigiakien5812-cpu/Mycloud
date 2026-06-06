from flask import Flask, request, send_from_directory, redirect, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET"])
def home():

    files = os.listdir(UPLOAD_FOLDER)

    html = """
    <html>

    <head>

    <title>My Cloud</title>

    <style>

    body{
        background:#0f172a;
        color:white;
        font-family:Arial;
        padding:20px;
    }

    .card{
        background:#1e293b;
        border-radius:15px;
        padding:15px;
        margin-bottom:15px;
    }

    button{
        background:#2563eb;
        color:white;
        border:none;
        padding:8px 12px;
        border-radius:8px;
        margin-top:5px;
        cursor:pointer;
    }

    button:hover{
        background:#1d4ed8;
    }

    input{
        width:100%;
        padding:8px;
        border-radius:8px;
        margin-top:5px;
    }

    a{
        color:#60a5fa;
        text-decoration:none;
    }

    img{
        max-width:200px;
        border-radius:10px;
        margin-top:10px;
    }

    progress {
        width: 100%;
        height: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    
    progress::-webkit-progress-bar {
        background-color: #334155;
        border-radius: 8px;
    }
    
    progress::-webkit-progress-value {
        background-color: #2563eb;
        border-radius: 8px;
    }

    </style>

    </head>

    <body>

    <h1>☁ My Cloud</h1>

    <div class="card">

    <input type="file" id="fileInput">

    <br><br>

    <button id="uploadBtn" onclick="startUpload()">
    Upload
    </button>

    <div id="progressContainer" style="display: none; margin-top: 15px;">
        <progress id="progressBar" value="0" max="100"></progress>
        <div style="margin-top: 5px; font-size: 14px; color: #94a3b8;">
            <span id="progressText">0%</span> - <span id="status">Đang chuẩn bị...</span>
        </div>
    </div>

    </div>

    <div class="card">

    <h2>📁 File của bạn</h2>
    """

    for f in files:

        path = os.path.join(UPLOAD_FOLDER, f)
        
        try:
            size = round(os.path.getsize(path) / 1024, 2)
        except:
            size = 0

        link = f"/download/{f}"

        html += f"""

        <div class="card">

        <b>{f}</b>

        <br>

        📦 {size} KB

        <br><br>

        <a href="{link}">
        ⬇ Tải xuống
        </a>

        |

        <a href="/delete/{f}">
        🗑 Xóa
        </a>

        <br><br>

        <input
        id="{f}"
        value="{link}"
        readonly>

        <button
        onclick="copyLink('{f}')">
        Copy Link
        </button>

        """

        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):

            html += f"""
            <br><br>

            <img src="/view/{f}">
            """

        html += "</div>"

    html += """

    </div>

    <script>
    
    const CHUNK_SIZE = 1024 * 1024; // Cắt nhỏ file thành từng cục 1MB
    const MAX_RETRIES = 5;         // Nếu rớt mạng, tự động up lại tối đa 5 lần

    function startUpload(){
        let fileInput = document.getElementById("fileInput");
        let file = fileInput.files[0];

        if(!file){
            alert("Chọn file đi 🗿");
            return;
        }

        document.getElementById("uploadBtn").disabled = true; // Khóa nút tránh bấm trùng
        document.getElementById("progressContainer").style.display = "block";
        document.getElementById("progressBar").value = 0;
        document.getElementById("progressText").innerText = "0%";
        document.getElementById("status").innerText = "Đang kết nối...";
        document.getElementById("status").style.color = "#94a3b8";

        // Bắt đầu up mảnh đầu tiên (start = 0), số lần thử lại bằng 0
        uploadChunk(file, 0, 0);
    }

    function uploadChunk(file, start, retries) {
        let end = Math.min(start + CHUNK_SIZE, file.size);
        let chunk = file.slice(start, end);

        let formData = new FormData();
        formData.append("file", chunk);
        formData.append("filename", file.name);
        formData.append("offset", start); // Gửi vị trí byte để server biết đường xếp mảnh

        let xhr = new XMLHttpRequest();

        // Tính toán số % dựa trên tổng số byte đã truyền thành công
        xhr.upload.addEventListener("progress", function(e){
            if(e.lengthComputable){
                let percent = Math.round(((start + e.loaded) / file.size) * 100);
                document.getElementById("progressBar").value = percent;
                document.getElementById("progressText").innerText = percent + "%";
                if(percent < 100) {
                    document.getElementById("status").innerText = "Đang tải lên...";
                    document.getElementById("status").style.color = "#94a3b8";
                }
            }
        });

        // Khi up xong mảnh hiện tại
        xhr.onload = function(){
            if(xhr.status == 200){
                if (end < file.size) {
                    // Up tiếp mảnh tiếp theo, reset số lần thử lại về 0
                    uploadChunk(file, end, 0);
                } else {
                    document.getElementById("status").innerText = "Upload xong xuôi nhen! Đang F5...";
                    document.getElementById("status").style.color = "#4ade80"; 
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                }
            } else {
                // Server báo lỗi (Ví dụ lỗi 502, 504 do nghẽn mạng) -> Kích hoạt tự động thử lại
                handleRetry(file, start, retries, "Lỗi phản hồi (" + xhr.status + ")");
            }
        };

        // Khi mạng chập chờn mất kết nối giữa chừng
        xhr.onerror = function(){
            handleRetry(file, start, retries, "Mạng chập chờn");
        };

        xhr.open("POST", "/upload");
        xhr.send(formData);
    }

    // Hàm xử lý tự động up lại mảnh bị lỗi
    function handleRetry(file, start, retries, reason) {
        if (retries < MAX_RETRIES) {
            let nextRetry = retries + 1;
            document.getElementById("status").innerText = reason + `... Đang tự động thử lại lần ${nextRetry}/${MAX_RETRIES}`;
            document.getElementById("status").style.color = "#f59e0b"; // Đổi chữ màu cam cảnh báo
            
            // Đợi 2 giây cho mạng ổn định rồi up lại đúng cái mảnh vừa lỗi
            setTimeout(function() {
                uploadChunk(file, start, nextRetry);
            }, 2000);
        } else {
            document.getElementById("status").innerText = "Thất bại liên tiếp! Vui lòng kiểm tra lại mạng mạng.";
            document.getElementById("status").style.color = "#f87171";
            document.getElementById("uploadBtn").disabled = false; // Mở lại nút bấm
        }
    }

    function copyLink(id){
        var text = document.getElementById(id);
        text.select();
        navigator.clipboard.writeText(window.location.origin + text.value);
        alert("Đã copy link");
    }

    </script>

    </body>

    </html>
    """

    return html


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    filename = request.form.get("filename")
    offset = int(request.form.get("offset", 0))

    if not file or not filename:
        return jsonify({"status": "error"}), 400

    path = os.path.join(UPLOAD_FOLDER, filename)

    # Chế độ mở file thông minh để chống hỏng file khi có Auto-Retry
    if offset == 0:
        mode = "wb"  # Mảnh đầu tiên: Tạo file mới tinh (Ghi đè nếu trùng tên cũ)
    else:
        mode = "r+b" # Mảnh tiếp theo: Mở file đang có sẵn để ghi tiếp vào giữa

    with open(path, mode) as f:
        if offset > 0:
            f.seek(offset) # Nhảy đúng đến vị trí byte bị thiếu để ghi, bất chấp việc bị up lại mảnh cũ
        f.write(file.read())

    return jsonify({"status": "success"})


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/view/<filename>")
def view(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/delete/<filename>")
def delete(filename):
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
