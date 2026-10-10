import os
import tempfile
import subprocess
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>AudioConvert</title>
      <style>
        body {
          margin: 0;
          background: #0b1020;
          color: white;
          font-family: Arial, sans-serif;
          display: grid;
          place-items: center;
          min-height: 100vh;
        }
        main {
          width: 85%;
          max-width: 480px;
          padding: 25px;
          background: #151c30;
          border-radius: 18px;
        }
        h1 { color: #ff4757; }
        p { color: #b5bfd3; line-height: 1.6; }
        input, button {
          width: 100%;
          box-sizing: border-box;
          margin-top: 15px;
          padding: 14px;
          border-radius: 9px;
        }
        input { background: #0b1020; color: white; }
        button {
          border: 0;
          background: #ff4757;
          color: white;
          font-weight: bold;
        }
      </style>
    </head>
    <body>
      <main>
        <h1>AudioConvert</h1>
        <p>Konversi file audio menjadi MP3.</p>
        <form action="/convert" method="post" enctype="multipart/form-data">
          <input type="file" name="audio" accept="audio/*" required>
          <button type="submit">Konversi ke MP3</button>
        </form>
        <p>Gunakan file audio yang kamu miliki atau diizinkan untuk dikonversi.</p>
      </main>
    </body>
    </html>
    """

@app.route("/convert", methods=["POST"])
def convert():
    uploaded = request.files.get("audio")

    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Pilih file audio terlebih dahulu."}), 400

    if not uploaded.filename.lower().endswith(
        (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".webm")
    ):
        return jsonify({"error": "Format file tidak didukung."}), 400

    with tempfile.TemporaryDirectory() as directory:
        source = os.path.join(directory, "input_audio")
        output = os.path.join(directory, "output.mp3")

        uploaded.save(source)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-nostdin", "-v", "error",
                    "-i", source,
                    "-vn", "-codec:a", "libmp3lame",
                    "-q:a", "2", output
                ],
                check=True,
                timeout=120
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return jsonify({
                "error": "Konversi gagal. Pastikan FFmpeg tersedia di server."
            }), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Proses konversi terlalu lama."}), 504

        return send_file(
            output,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="audioconvert.mp3"
        )

@app.errorhandler(413)
def too_large(error):
    return jsonify({"error": "Ukuran file maksimal 50 MB."}), 413

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)