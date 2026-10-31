import io
import os
import uuid
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)
from google.cloud import firestore, storage

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "replace-with-a-secure-random-key")

# Passwords & Admin username configuration
GALLERY_PASSWORD = os.environ.get("GALLERY_PASSWORD", "admin123")
configured_admin = os.environ.get("ADMIN_NAME", "admin").strip().lower()
ADMIN_USERNAMES = {"admin", configured_admin}

storage_client = storage.Client()
firestore_client = firestore.Client()
BUCKET_NAME = os.environ.get("BUCKET_NAME")

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Photo Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f7fa; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: white; padding: 30px 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 360px; text-align: center; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 15px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0056b3; }
        .error { color: #d9534f; margin-bottom: 15px; font-size: 14px; }
        .hint { font-size: 12px; color: #666; margin-top: 12px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 Protected Gallery</h2>
        <p>Enter your username and gallery password.</p>

        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="error">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}

        <form method="POST">
            <input type="text" name="username" placeholder="Username (use 'admin ’)" required autofocus>
            <input type="password" name="password" placeholder="Gallery Password" required>
            <button type="submit">Log In</button>
        </form>
        <p class="hint">Log in as <b>chiho</b> or <b>admin</b> for master delete privileges.</p>
    </div>
</body>
</html>
"""

GALLERY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Photo Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; background: #f5f7fa; }
        .header-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: white; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
        .user-tag { font-size: 14px; color: #444; margin-right: 15px; }
        .admin-badge { background: #007bff; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }
        .logout-link { text-decoration: none; color: #d9534f; font-weight: bold; padding: 6px 14px; border: 1px solid #d9534f; border-radius: 5px; font-size: 13px; }
        .logout-link:hover { background: #d9534f; color: white; }
        .upload-box { background: white; padding: 25px; border-radius: 10px; margin-bottom: 30px; }
        input[type="text"], input[type="file"] { margin: 10px 0; padding: 8px; }
        button.btn-upload { padding: 10px 20px; border: none; border-radius: 5px; background: #28a745; color: white; cursor: pointer; }
        button.btn-upload:hover { background: #218838; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
        .photo { background: white; padding: 12px; border-radius: 10px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .photo img { width: 100%; height: 220px; object-fit: cover; border-radius: 8px; cursor: pointer; transition: transform 0.2s ease, opacity 0.2s ease; }
        .photo img:hover { opacity: 0.9; transform: scale(1.02); }
        .photo-details { margin-top: 10px; }
        .photo-actions { margin-top: 12px; display: flex; justify-content: flex-end; min-height: 32px; }
        .btn-delete { background: #ffeded; color: #d9534f; border: 1px solid #d9534f; border-radius: 4px; padding: 6px 12px; font-size: 12px; cursor: pointer; font-weight: bold; }
        .btn-delete:hover { background: #d9534f; color: white; }
        .modal { display: none; position: fixed; z-index: 1000; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.85); justify-content: center; align-items: center; flex-direction: column; }
        .modal-content { max-width: 90vw; max-height: 80vh; border-radius: 6px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6); object-fit: contain; }
        .modal-caption { color: #fff; margin-top: 15px; font-size: 1.1rem; text-align: center; }
        .modal-close { position: absolute; top: 20px; right: 30px; color: #fff; font-size: 35px; font-weight: bold; cursor: pointer; }
        .modal-close:hover { color: #bbb; }
    </style>
</head>
<body>

<div class="header-bar">
    <h2 style="margin: 0; font-size: 20px;">📸 Photo Gallery</h2>
    <div>
        <span class="user-tag">
            Logged in as: <strong>{{ current_user }}</strong>
            {% if is_admin %}
                <span class="admin-badge">Admin</span>
            {% endif %}
        </span>
        <a href="/logout" class="logout-link">Logout</a>
    </div>
</div>

<div class="upload-box">
    <h2>Upload a photo</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="hidden" name="upload_id" value="{{ upload_id }}">
        <p style="margin: 0 0 10px 0; color: #555;">Posting as: <strong>{{ current_user }}</strong></p>
        <input type="text" name="caption" placeholder="Photo caption" required style="width: 60%;"><br>
        <input type="file" name="photo" accept="image/*" required><br>
        <button type="submit" class="btn-upload">Upload Photo</button>
    </form>
</div>

<h2>Gallery</h2>

<div class="gallery">
{% for photo in photos %}
    <div class="photo">
        <div>
            <img src="/image/{{ photo.filename }}" alt="{{ photo.caption }}" onclick="openModal(this)">
            <div class="photo-details">
                <h3 style="margin: 8px 0 4px 0; font-size: 16px;">{{ photo.caption }}</h3>
                <p style="margin: 0; color: #666; font-size: 13px;">Uploaded by: {{ photo.uploader or 'Unknown' }}</p>
            </div>
        </div>
        <div class="photo-actions">
            {% if is_admin or (photo.uploader and photo.uploader|trim|lower == current_user|trim|lower) %}
                <form method="POST" action="/delete/{{ photo.id }}" onsubmit="return confirm('Permanently delete this photo?');">
                    <button type="submit" class="btn-delete">Delete</button>
                </form>
            {% endif %}
        </div>
    </div>
{% endfor %}
</div>

<div id="imageModal" class="modal" onclick="closeModal(event)">
    <span class="modal-close" onclick="forceCloseModal()">&times;</span>
    <img class="modal-content" id="modalImg">
    <div id="modalCaption" class="modal-caption"></div>
</div>

<script>
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImg");
    const modalCaption = document.getElementById("modalCaption");
    function openModal(imgElement) {
        modal.style.display = "flex";
        modalImg.src = imgElement.src;
        modalCaption.textContent = imgElement.alt;
    }
    function closeModal(event) { if (event.target === modal) modal.style.display = "none"; }
    function forceCloseModal() { modal.style.display = "none"; }
    document.addEventListener("keydown", function(event) { if (event.key === "Escape") modal.style.display = "none"; });
</script>
</body>
</html>
"""


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated") or not session.get("user"):
            session.clear()
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        submitted_user = request.form.get("username", "").strip()
        submitted_pw = request.form.get("password", "")

        if submitted_pw == GALLERY_PASSWORD and submitted_user:
            session["authenticated"] = True
            session["user"] = submitted_user
            session["is_admin"] = submitted_user.lower() in ADMIN_USERNAMES
            return redirect(url_for("gallery"))

        flash("Incorrect username or password.")

    return render_template_string(LOGIN_HTML)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def gallery():
    bucket = storage_client.bucket(BUCKET_NAME)
    current_user = session.get("user", "")
    is_admin = session.get("is_admin", False)

    if request.method == "POST":
        photo = request.files.get("photo")
        caption = request.form.get("caption", "").strip()
        upload_id = request.form.get("upload_id", "").strip()

        if photo and photo.filename and upload_id:
            photo_ref = firestore_client.collection("photos").document(upload_id)
            existing = photo_ref.get()

            if not existing.exists:
                extension = os.path.splitext(photo.filename)[1].lower()
                filename = f"{upload_id}{extension}"

                blob = bucket.blob(filename)
                blob.upload_from_file(photo, content_type=photo.content_type)

                photo_ref.set({
                    "id": upload_id,
                    "filename": filename,
                    "caption": caption,
                    "uploader": current_user,
                    "bucket": BUCKET_NAME,
                    "content_type": photo.content_type,
                    "uploaded_at": firestore.SERVER_TIMESTAMP,
                })

            return redirect(url_for("gallery"))

    photos = []
    photos_ref = (
        firestore_client.collection("photos")
        .order_by("uploaded_at", direction=firestore.Query.DESCENDING)
    )

    for doc in photos_ref.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        photos.append(data)

    return render_template_string(
        GALLERY_HTML,
        photos=photos,
        upload_id=str(uuid.uuid4()),
        current_user=current_user,
        is_admin=is_admin,
    )


@app.route("/delete/<photo_id>", methods=["POST"])
@login_required
def delete_photo(photo_id):
    photo_ref = firestore_client.collection("photos").document(photo_id)
    doc = photo_ref.get()

    if doc.exists:
        data = doc.to_dict()
        uploader = data.get("uploader", "")
        current_user = session.get("user", "")
        is_admin = session.get("is_admin", False)

        can_delete = is_admin or (uploader and uploader.strip().lower() == current_user.strip().lower())

        if not can_delete:
            return "Forbidden: You are not authorized to delete this photo.", 403

        filename = data.get("filename")
        if filename:
            try:
                bucket = storage_client.bucket(BUCKET_NAME)
                blob = bucket.blob(filename)
                if blob.exists():
                    blob.delete()
            except Exception as e:
                print(f"Error deleting blob {filename}: {e}")

        photo_ref.delete()

    return redirect(url_for("gallery"))


@app.route("/image/<filename>")
@login_required
def image(filename):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    image_data = blob.download_as_bytes()

    return send_file(io.BytesIO(image_data), mimetype=blob.content_type)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
