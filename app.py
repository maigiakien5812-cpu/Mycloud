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

    /* Định dạng thanh tiến trình */
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

    <button onclick="uploadFile()">
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

        size = round(os.path.getsize(path) / 1024, 2)

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

    function uploadFile(){
        let fileInput = document.getElementById("fileInput");
        let file = fileInput.files[0];

        if(!file){
            alert("Chọn file đi 🗿");
            return;
        }

        // Hiện thanh tiến trình và reset thông số
        document.getElementById("progressContainer").style.display = "block";
        document.getElementById("progressBar").value = 0;
        document.getElementById("progressText").innerText = "0%";
        document.getElementById("status").innerText = "Đang tải lên...";
        document.getElementById("status").style.color = "#94a3b8";

        let formData = new FormData();
        formData.append("file", file);

        let xhr = new XMLHttpRequest();

        // Bắt sự kiện cập nhật % tiến trình
        xhr.upload.addEventListener("progress", function(e){
            if(e.lengthComputable){
                let percent = Math.round((e.loaded / e.total) * 100);
                document.getElementById("progressBar").value = percent;
                document.getElementById("progressText").innerText = percent + "%";
            }
        });

        // Xử lý khi upload hoàn tất
        xhr.onload = function(){
            if(xhr.status == 200){
                document.getElementById("status").innerText = "Upload xong xuôi! Đang làm mới...";
                document.getElementById("status").style.color = "#4ade80"; // Chữ màu xanh lá
                
                // Đợi 1.2 giây để người dùng kịp thấy 100% rồi mới F5 trang
                setTimeout(function() {
                    location.reload();
                }, 1200);
            } else {
                document.getElementById("status").innerText = "Lỗi upload rồi nhen!";
                document.getElementById("status").style.color = "#f87171"; // Chữ màu đỏ
            }
        };

        xhr.open("POST", "/upload");
        xhr.send(formData);
    }

    function copyLink(id){

        var text = document.getElementById(id);

        text.select();

        navigator.clipboard.writeText(
            window.location.origin +
            text.value
        );

        alert("Đã copy link");
    }

    </script>

    </body>

    </html>
    """

    return html


# API riêng để xử lý Upload qua JavaScript
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"status": "error"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"status": "error"}), 400

    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return jsonify({"status": "success"})


@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


@app.route("/view/<filename>")
def view(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


@app.route("/delete/<filename>")
def delete(filename):

    path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    if os.path.exists(path):
        os.remove(path)

    return redirect("/")


if __name__ == "__main__":
    # Đã sửa lỗi thụt lề (IndentationError) ở đây luôn cho bồ nhé
    app.run(
        host="0.0.0.0",
        port=5000
)
