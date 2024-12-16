from flask import Flask, render_template_string, request, jsonify
import os
from google.cloud import vision, translate_v2 as translate
from werkzeug.utils import secure_filename
from google.cloud import speech

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google Cloud API clients
vision_client = vision.ImageAnnotatorClient()
translate_client = translate.Client()

# Google Cloud API clients

speech_client = speech.SpeechClient()
translate_client = translate.Client()

# Define acceptable audio formats and their encodings

AUDIO_FORMATS = {
    'mp3': speech.RecognitionConfig.AudioEncoding.MP3,
    'wav': speech.RecognitionConfig.AudioEncoding.LINEAR16,  # For WAV files
    'flac': speech.RecognitionConfig.AudioEncoding.FLAC,  # For FLAC files
}

# Home Page Route
@app.route('/')
def home():
    return render_template_string(HOME_PAGE)

# Image Text Translator Route
@app.route('/image_text_translator')
def image_text_translator():
    return render_template_string(IMAGE_TEXT_TRANSLATOR_PAGE)

# Audio Text Translator Route
@app.route('/audio_text_translator')
def audio_text_translator():
    return render_template_string(AUDIO_TEXT_TRANSLATOR_PAGE)

# Video Text Translator Route
@app.route('/video_text_translator')
def video_text_translator():
    return render_template_string(VIDEO_TEXT_TRANSLATOR_PAGE)

# Image Upload and Translation
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text from image
    with open(filepath, 'rb') as image_file:
        content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.text_detection(image=image)
        texts = response.text_annotations

    if not texts:
        return jsonify({'error': 'No text found in image'}), 400
    original_text = texts[0].description

    # Translate to English by default
    translation = translate_client.translate(original_text, target_language='en')
    translated_text = translation['translatedText']
    return jsonify({'translated_text': translated_text})

@app.route('/translate', methods=['POST'])
def translate_text():
    original_text = request.form['text']
    target_language = request.form['language']
    translation = translate_client.translate(
        original_text, target_language=target_language
    )
    return jsonify({'translated_text': translation['translatedText']})

# Audio Upload and Translation (similar logic for audio as image)
@app.route('/upload-audio', methods=['POST'])
def upload_audio():

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400 
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400 
    source_language = request.form.get('source_language')

    if not source_language:
        return jsonify({'error': 'No source language selected'}), 400 
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
 
    # Detect the file extension

    file_extension = filename.split('.')[-1].lower()
 
    # Ensure the file format is supported

    if file_extension not in AUDIO_FORMATS:
        return jsonify({'error': 'Unsupported audio format'}), 400
 
    # Get the appropriate encoding for the file format

    encoding = AUDIO_FORMATS[file_extension]
 
    # Open the audio file and read its content

    with open(filepath, 'rb') as audio_file:
        content = audio_file.read()
 
    # Set up audio and recognition config

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=encoding,  # Use the encoding based on the file format
        sample_rate_hertz=16000,
        language_code=source_language,
    )
 
    # Perform speech-to-text transcription

    response = speech_client.recognize(config=config, audio=audio) 
    if not response.results:
        return jsonify({'error': 'No speech detected in audio'}), 400
 
    # Get the transcribed text

    transcribed_text = response.results[0].alternatives[0].transcript
 
    # Translate the transcribed text to English, Hindi, and Telugu

    try:
        translations = {}
        for lang in ['en', 'hi', 'te']:
            translation = translate_client.translate(transcribed_text, target_language=lang)
            translations[lang] = translation['translatedText'] 
        return jsonify({'translated_text': translations})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Home Page HTML
HOME_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home - Translator App</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .btn { padding: 15px 30px; font-size: 18px; margin: 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        .btn:hover { background-color: #2980b9; }
    </style>
</head>
<body>
    <h1>Welcome to the Translator App</h1>
    <p>Select an option below to proceed:</p>
    <a href="/image_text_translator" class="btn">Image Text Translator</a>
    <a href="/audio_text_translator" class="btn">Audio Text Translator</a>
    <a href="/video_text_translator" class="btn">Video Text Translator</a>
</body>
</html>
'''

# Image Text Translator HTML
IMAGE_TEXT_TRANSLATOR_PAGE = '''
<!DOCTYPE html>
<html>
<head>
<title>Image Translator</title>
<style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .image-preview {
            width: 100%;
            max-height: 300px;
            object-fit: contain;
            border: 1px solid #ccc;
            margin-bottom: 10px;
        }

        textarea {
            width: 100%;
            height: 150px;
            margin-top: 10px;
        }

        .row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .column {
            flex: 1;
            padding: 10px;
        }
</style>
</head>
<body>
<div class="container">
<h1>Image Translator</h1>
<form id="upload-form" action="/upload" method="post" enctype="multipart/form-data">
<label for="file">Upload an image:</label><br>
<input type="file" name="file" id="file" accept="image/*" required><br><br>
<img id="image-preview" class="image-preview" alt="Image preview will appear here">
</form>

 <h3>Translate to:</h3>
<form id="translate-form">
<select id="language">
<option value="en" selected>English</option>
<option value="hi">Hindi</option>
<option value="te">Telugu</option>
</select>

<h3>Translated Text:</h3>
<textarea id="translated-text" readonly></textarea>

</form>
</div>       
 
    <script>
        const fileInput = document.getElementById('file');
        const imagePreview = document.getElementById('image-preview');
        const translatedTextArea = document.getElementById('translated-text');
        const languageSelect = document.getElementById('language');

        fileInput.onchange = async () => {
            const file = fileInput.files[0];
            if (file) {
                // Preview the image
                const reader = new FileReader();
                reader.onload = () => {
                    imagePreview.src = reader.result;
                };

                reader.readAsDataURL(file);
                // Upload the image and get translated text
                const formData = new FormData();
                formData.append('file', file);
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.error) {
                    alert(data.error);
                } else {
                    translatedTextArea.value = data.translated_text;
                }
            }
        };
 
        languageSelect.onchange = async () => {
            const text = translatedTextArea.value;
            const language = languageSelect.value;
            const response = await fetch('/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ text, language })
            });

            const data = await response.json();
            translatedTextArea.value = data.translated_text;
        };
</script>
<button onclick="window.location.href='/'">Back to Home</button>
</body>
</html>
'''

# Audio Text Translator HTML (Similar to Image Translator)
AUDIO_TEXT_TRANSLATOR_PAGE = '''
<!DOCTYPE html>
<html>
<head>
<title>Audio Translator</title>
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
        border: 1px solid #ccc;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    .audio-preview {
        width: 100%;
        margin-bottom: 10px;
    }
    textarea {
        width: 100%;
        height: 150px;
        margin-top: 10px;
    }

    /* Loader styling */

    .loader {
        display: none;
        border: 8px solid #f3f3f3;
        border-top: 8px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 2s linear infinite;
        margin: 20px auto;
    }
 
    /* Overlay to disable screen */

    .overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 100;
        opacity: 0.5;
    }
 
    /* Progress bar styling */

    .progress-bar {
        width: 100%;
        height: 10px;
        background-color: #f3f3f3;
        margin-top: 20px;
        border-radius: 5px;
    }
 
    .progress {

        height: 100%;
        background-color: #3498db;
        width: 0;
        border-radius: 5px;
    }
 
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
</head>
<body>
<div class="container">
<h1>Audio Translator</h1>
<form id="upload-form" action="/upload-audio" method="post" enctype="multipart/form-data">
<label for="file">Upload an audio file:</label><br>
<input type="file" name="file" id="file" accept="audio/*" required><br><br>
<audio id="audio-player" controls class="audio-preview" style="display:none;"></audio><br>
<label for="source-language">Select the language of the audio:</label><br>
<select id="source-language" name="source_language" required>
<option value="en-US">English</option>
<option value="hi-IN">Hindi</option>
<option value="te-IN">Telugu</option>
<option value="ta-IN">Tamil</option>
<option value="ml-IN">Malayalam</option>
<option value="kn-IN">Kannada</option>
<option value="bn-IN">Bengali</option>
<option value="gu-IN">Gujarati</option>
<option value="mr-IN">Marathi</option>
</select><br><br>
<button type="submit">Upload and Translate</button>
</form>
<!-- Loader -->
<div class="loader" id="loader"></div>
 
<!-- Overlay to disable interaction -->
<div class="overlay" id="overlay"></div>
 
<!-- Progress bar -->
<div class="progress-bar" id="progress-bar">
<div class="progress" id="progress"></div>
</div>
 
<h3>Translated Text:</h3>
<select id="target-language">
<option value="en">English</option>
<option value="hi">Hindi</option>
<option value="te">Telugu</option>
</select>
<textarea id="translated-text" readonly></textarea>
</div>
<script>

    const fileInput = document.getElementById('file');
    const audioPlayer = document.getElementById('audio-player');
    const translatedTextArea = document.getElementById('translated-text');
    const uploadForm = document.getElementById('upload-form');
    const targetLanguage = document.getElementById('target-language');
    const loader = document.getElementById('loader');  // Reference to the loader
    const overlay = document.getElementById('overlay');  // Reference to the overlay
    const progressBar = document.getElementById('progress');  // Progress bar
    const progressBarContainer = document.getElementById('progress-bar');  // Progress bar container
    loader.style.display = 'none';
    overlay.style.display = 'none';
    progressBarContainer.style.display = 'none';
    let translations = {}; 
    fileInput.onchange = () => {
        const file = fileInput.files[0];
        if (file) {
            const objectURL = URL.createObjectURL(file);
            audioPlayer.src = objectURL;
            audioPlayer.style.display = 'block';
        }
    };

    uploadForm.onsubmit = async (event) => {
        event.preventDefault();

        // Show the loader and overlay when the form is submitted
        loader.style.display = 'block';
        overlay.style.display = 'block';
        progressBarContainer.style.display = 'block';  // Show progress bar container 
        const formData = new FormData(uploadForm); 

        // Track the percentage of progress (for demo purposes, using setTimeout)
        let progress = 0;

        const updateProgress = setInterval(() => {
            if (progress < 100) {
                progress += 5;  // Update progress (increased by 5% at a time for demo)
                progressBar.style.width = progress + '%';
            }
        }, 1000); 
        try {
            const response = await fetch('/upload-audio', { method: 'POST', body: formData });
            const data = await response.json(); 
            clearInterval(updateProgress);  // Stop the progress update once we get the response 
            if (data.error) {
                alert(data.error);
            } else {
                translations = data.translated_text;
                translatedTextArea.value = translations['en'] || 'N/A'; // Default to English
            }

        } catch (error) {
            clearInterval(updateProgress);  // Stop the progress update if an error occurs
            alert("Error: " + error.message);            
        } finally {

            // Hide the loader, overlay, and progress bar once the process is complete

            loader.style.display = 'none';
            overlay.style.display = 'none';
            progressBarContainer.style.display = 'none';
        }

    };

    targetLanguage.onchange = () => {
        const selectedLanguage = targetLanguage.value;
        translatedTextArea.value = translations[selectedLanguage] || 'N/A';
    };
</script>
<button onclick="window.location.href='/'">Back to Home</button>
</body>
</html>
'''

# Video Text Translator HTML (Similar to Audio and Image pages)
VIDEO_TEXT_TRANSLATOR_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Video Translator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }
        .video-preview { width: 100%; margin-bottom: 10px; }
        textarea { width: 100%; height: 150px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Translator</h1>
        <form id="upload-form" action="/upload-video" method="post" enctype="multipart/form-data">
            <label for="file">Upload a video file:</label><br>
            <input type="file" name="file" id="file" accept="video/*" required><br><br>
            <video id="video-player" controls class="video-preview" style="display:none;"></video><br>
        </form>
        <h3>Translated Text:</h3>
        <textarea id="translated-text" readonly></textarea>
    </div>
    <script>
        const fileInput = document.getElementById('file');
        const videoPlayer = document.getElementById('video-player');
        const translatedTextArea = document.getElementById('translated-text');
        fileInput.onchange = async () => {
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch('/upload-video', { method: 'POST', body: formData });
            const data = await response.json();
            translatedTextArea.value = data.translated_text;
            videoPlayer.src = data.video_url;
            videoPlayer.style.display = 'block';
        };
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
