import cv2
from PIL import Image
import sys
import numpy as np
import moviepy.editor as mp
import uuid
import os
from werkzeug import secure_filename
from flask import Flask ,render_template ,request, url_for, send_from_directory


app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['mp4'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



def conv2dto3d(image):
    im1 = image
    im2 = im1.copy()

    parallax = 10
    im1 = im1.rotate(0, translate=(parallax, 0))
    im2 = im2.rotate(0, translate=(-parallax, 0))

    im = Image.blend(im1, im2, 0.5)
    return im


def get_sound(input_video, sound):
    clip_input = mp.VideoFileClip(input_video).subclip()
    clip_input.audio.write_audiofile(sound)


def set_audio(output_video, sound):
    clip_output = mp.VideoFileClip(output_video).subclip()
    clip_output.write_videofile(output_video.replace(".avi", ".mp4"), audio=sound)

def convert(input_video):
    input_video = "./uploads/" + input_video.filename
    file_id = str(uuid.uuid4())
    output_video = "./static/output" + file_id +".avi"
    sound = "./static/audio" + file_id +".mp3"
    video = cv2.VideoCapture(input_video)
    if not video.isOpened():
        print("動画が読み込めていません")
        sys.exit(1)

    # 幅
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    # 高さ
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # 総フレーム数
    count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    # fps
    fps = int(video.get(cv2.CAP_PROP_FPS))
    # アウトプットするオブジェクト
    out = cv2.VideoWriter(
        output_video, cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height)
    )

    # 音声取得
    get_sound(input_video, sound)

    # 変換処理
    while True:
        ret, frame = video.read()
        if ret:
            # cv2 → PIL
            image = Image.fromarray(frame)
            # 2d → 3d
            conv_image = conv2dto3d(image)
            # PIL → cv2
            result = np.asarray(conv_image)
            out.write(result)
        else:
            break

    video.release()
    out.release()
    cv2.destroyAllWindows()

    set_audio(output_video, sound)

    return file_id


@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')

@app.route("/", methods=["POST"])
def input():
    movie = request.files['movie']
    if movie :
        filename = secure_filename(movie.filename)
        movie.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    file_id = convert(movie)
    movie_path = "./static/output"+ file_id +".mp4"
    named_path = "./uploads/" + filename.split(".")[0] + file_id + "." + filename.split(".")[1]
    os.remove("./uploads/" + filename)
    os.remove("./static/output" + file_id + ".avi")
    os.remove("./static/audio" + file_id + ".mp3")
    return render_template('movie.html', file=movie_path)


if __name__ == '__main__':
    app.debug = True
    app.run(debug=True, host='0.0.0.0', port=8000)