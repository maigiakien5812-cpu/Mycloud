from flask import Flask, request, send_from_directory, redirect
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        if "file" in request.files:

            file = request.files["file"]

            if file.filename != "":
                file.save(
                    os.path.join(
                        UPLOAD_FOLDER,
                        file.filename
                    )
                )

        return redirect("/")

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

    </style>

    </head>

    <body>

    <h1>☁ My Cloud</h1>

    <div class="card">

    <form method="POST" enctype="multipart/form-data">

    <input type="file" name="file">

    <br><br>

    <button type="submit">
    Upload
    </button>

    </form>

    </div>

    <div class="card">

    <h2>📁 File của bạn</h2>
    """

    for f in files:

        path = os.path.join(
            UPLOAD_FOLDER,
            f
        )

        size = round(
            os.path.getsize(path) / 1024,
            2
        )

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

        if f.lower().endswith(
            (
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp"
            )
        ):

            html += f"""
            <br><br>

            <img src="/view/{f}">
            """

        html += "</div>"

    html += """

    </div>

    <script>

    function copyLink(id){

        var text =
        document.getElementById(id);

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
    app.run(
        host="0.0.0.0",
        port=5000
)
