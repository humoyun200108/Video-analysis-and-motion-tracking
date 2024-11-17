from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename
from object_detection import process_image, process_video
import uuid
from threading import Thread

app = Flask(__name__)

# Maksimal fayl hajmi (100 MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Ruxsat etilgan fayl turlari
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'

# Papkalarni yaratish
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Progressni saqlash uchun global o'zgaruvchi
progress = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/progress/<task_id>')
def progress_status(task_id):
    # Progressni qaytarish
    prog = progress.get(task_id, 0)
    return jsonify({'progress': prog})

@app.route('/result/<task_id>')
def result(task_id):
    file_ext = progress.get(task_id + '_ext')
    original_filename = progress.get(task_id + '_original')
    result_filename = 'result_' + task_id + '.mp4'  # Fayl kengaytmasini '.mp4' qilib o'zgartirdik
    result_url = url_for('static', filename='results/' + result_filename)
    original_url = url_for('static', filename='uploads/' + original_filename)
    is_video = True  # Video fayli deb belgilanadi
    return render_template('result.html', original_file=original_url, result_file=result_url, is_video=is_video)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Fayl yuklanmadi.'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Fayl tanlanmadi.'})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # Fayl turini aniqlash
            file_ext = filename.rsplit('.', 1)[1].lower()

            # Foydalanuvchi uchun unikal task_id yaratamiz
            task_id = str(uuid.uuid4())
            progress[task_id] = 0  # Progressni boshlaymiz
            progress[task_id + '_ext'] = file_ext  # Fayl kengaytmasini saqlaymiz
            progress[task_id + '_original'] = filename  # Asl fayl nomini saqlaymiz

            # Natija faylining yo'li
            result_filename = 'result_' + task_id + '.mp4'  # '.mp4' kengaytmasi
            result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)

            # Fayl turiga qarab qayta ishlaymiz
            def process_task():
                try:
                    if file_ext in ['png', 'jpg', 'jpeg', 'gif']:
                        # Tasvirni qayta ishlash
                        process_image(upload_path, result_path)
                        progress[task_id] = 100
                    elif file_ext in ['mp4', 'avi', 'mov']:
                        # Videoni qayta ishlash
                        process_video(upload_path, result_path, task_id=task_id, progress_dict=progress)
                    else:
                        progress[task_id] = 'error'
                except Exception as e:
                    progress[task_id] = 'error'
                    print(f"Xatolik: {e}")
                finally:
                    # Agar progress 100% ga yetmagan bo'lsa, uni 100% ga o'rnatamiz
                    if progress.get(task_id, 0) < 100:
                        progress[task_id] = 100

            thread = Thread(target=process_task)
            thread.start()

            return jsonify({'task_id': task_id})
        else:
            return jsonify({'error': 'Ruxsat etilmagan fayl turi.'})
    return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
