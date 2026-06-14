#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove, new_session
from PIL import Image
import io
import os

app = Flask(__name__)
CORS(app)

print("⏳ جاري تحميل الموديل...")
try:
    session = new_session("u2net")
    print("✅ الموديل اتحمل بنجاح")
except Exception as e:
    print(f"⚠️ {e}")
    session = None


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    if 'image' not in request.files:
        return jsonify({'error': 'مفيش صورة'}), 400

    file = request.files['image']
    bg_color_name = request.form.get('bg_color', 'white')
    quality_option = request.form.get('quality', 'high')

    color_map = {'white': '#FFFFFF', 'light_gray': '#F5F5F5', 'transparent': None}
    hex_color = color_map.get(bg_color_name, bg_color_name if bg_color_name.startswith('#') else '#FFFFFF')

    try:
        img_bytes = file.read()
        print(f"📸 معالجة: {file.filename}")

        result_bytes = remove(img_bytes, session=session) if session else remove(img_bytes)
        result_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        output_buffer = io.BytesIO()

        if hex_color is None:
            result_image.save(output_buffer, format='PNG', optimize=True)
            mimetype = 'image/png'
        else:
            bg_rgb = hex_to_rgb(hex_color)
            background = Image.new("RGBA", result_image.size, (*bg_rgb, 255))
            final_image = Image.alpha_composite(background, result_image).convert("RGB")

            if quality_option == 'high':
                final_image.save(output_buffer, format='PNG', optimize=True)
                mimetype = 'image/png'
            else:
                final_image.save(output_buffer, format='JPEG', quality=90, optimize=True)
                mimetype = 'image/jpeg'

        output_buffer.seek(0)
        print("✅ تمت المعالجة")
        return send_file(output_buffer, mimetype=mimetype, as_attachment=False)

    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
