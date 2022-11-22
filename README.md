# Realsense stream with flask
This package is Realsense streaming application with flask.

By using this application, you can do QR code information, depth value and crack detection.

![rs Image](/image/rs_stream_with_flask.jpg)

## Operation confirmed environment
- Realsense D4XX
- Python 3.8.10
- Flask 2.1.2
- Bootstrap 4.x
- Werkzeug 2.1.1

<br>

## Installation

```
pip3 install flask
pip3 install pyrealsense2
sudo apt-get install libzbar-dev -y
pip3 install pyzbar
```

<br>

## Usage

If you want to change the header image, please replace "/static/background.jpg"

```
cd ./realsense_stream_with_flask/
python3 rs_stream_view.py
```

Running on http://localhost:5069 (Press CTRL+C to quit)

<br>

## License
This repository is licensed under the Apache 2.0, see LICENSE for details.