import pyrealsense2 as rs
import numpy as np
import cv2
import os
import datetime
from threading import Thread

from pyzbar.pyzbar import decode
from flask import *


app = Flask(__name__)

global color, qr, crack, depth_color, infra1, infra2, capture, rec_frame, rec, out
capture, switch, rec = 0, 1, 0
color, qr, crack, depth_color, infra1, infra2 = 0, 0, 0, 0, 0, 0


@app.route('/')
def index():
    return render_template('index.html',\
        title = "Realsense Stream with Flask", \
        message = "Realsense Stream with Flask",\
    )

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch
    if request.method == 'POST':
        global color, qr, crack, depth_color, infra1, infra2, rec, out
        if request.form.get('color') == 'Color':
            color, qr, crack, depth_color, infra1, infra2, =True, False, False, False, False, False
            print("color")
        elif request.form.get('qr') == 'QR':
            color, qr, crack, depth_color, infra1, infra2, = False, True, False, False, False, False
            print("qr")
        elif request.form.get('crack_detect') == 'Crack':
            color, qr, crack, depth_color, infra1, infra2, = False, False, True, False, False, False
            print("crack")
        elif request.form.get('depth_color') == 'DepthColor':
            color, qr, crack, depth_color, infra1, infra2, = False, False, False, True, False, False
            print("depth")
        elif  request.form.get('infra1') == 'Infra1':
            color, qr, crack, depth_color, infra1, infra2, = False, False, False, False, True, False
            print("infra1")
        elif  request.form.get('infra2') == 'Infra2':
            color, qr, crack, depth_color, infra1, infra2, = False, False, False, False, False, True
            print("infra2")

        elif request.form.get('click') == 'Screenshot':
            global capture
            capture=1

        elif  request.form.get('rec') == 'Start/Stop Recording':
            rec = not rec
            if(rec):
                now=datetime.datetime.now() 
                fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                out = cv2.VideoWriter('outut_{}.avi'.format(str(now).replace(":",'')), fourcc, 20, (640, 480))
                thread = Thread(target=record, args=[out,])
                thread.start()
            elif(rec==False):
                out.release()

    elif request.method=='GET':
        return render_template('index.html',\
            title = "Realsense Stream with Flask", \
            message = "Realsense Stream with Flask",\
        )
    return render_template('index.html',\
        title = "Realsense Stream with Flask", \
        message = "Realsense Stream with Flask",\
    )

def generate_frames():
    global out, capture,rec_frame
    while True:
        frames = pipeline.wait_for_frames()

        if(color):
            data_frame = frames.get_color_frame()
            data_image = np.asanyarray(data_frame.get_data())

        if(qr):
            data_frame = frames.get_color_frame()
            data_image = np.asanyarray(data_frame.get_data())
            # Update color and depth frames:
            depth_frame = frames.get_depth_frame()  # IMPORTANT!!
            depth_image = np.asanyarray(depth_frame.get_data())

            for barcode in decode(data_image):
                myData = barcode.data.decode('utf-8')
                pts =np.array([barcode.polygon],np.int32)
                cv2.polylines(data_image,[pts],True,(255,0,0),5)
                pts2 =barcode.rect
                center_x, center_y = int(pts2[0]+pts2[2]/2), int(pts2[1]+pts2[3]/2)
                distance = depth_frame.get_distance(center_x, center_y)
                dist_cm = round(distance*100, 2)
                circle_r = 15
                cv2.circle(data_image, (center_x, center_y), circle_r, (255,0,255), thickness=-1)
                cv2.putText(data_image,myData,(pts2[0],pts2[1]),cv2.FONT_HERSHEY_COMPLEX,1,(255,102,0),2)
                cv2.putText(data_image,
                    text='({}px, {}px, {}cm)'.format(center_x, center_y, dist_cm),
                    org=(center_x+circle_r, center_y),
                    fontFace=cv2.FONT_HERSHEY_COMPLEX,
                    fontScale=1.0,
                    color=(255,0,255),
                    thickness=2)

        if(crack):
            data_frame = frames.get_color_frame()
            frame = np.asanyarray(data_frame.get_data())

            grey_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(grey_frame, (5, 5), 0)
            edges = cv2.Canny(blur,100,200)

            # Morphological Closing Operator
            kernel = np.ones((5,5),np.uint8)
            closing = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            contours, hierarchy = cv2.findContours(closing,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

            data_image = cv2.drawContours(frame, contours, -1, (0,255,0), 3)

        if(depth_color):
            data_frame = frames.get_depth_frame()
            depth_image = np.asanyarray(data_frame.get_data())
            scaled_depth = cv2.convertScaleAbs(depth_image, alpha=0.03)
            data_image = cv2.applyColorMap(scaled_depth, cv2.COLORMAP_JET)

        if(infra1):
            data_frame = frames.get_infrared_frame(1) # Left IR Camera, it allows 1, 2 or no input
            data_image = np.asanyarray(data_frame.get_data())

        if(infra2):
            data_frame = frames.get_infrared_frame(2) # Left IR Camera, it allows 1, 2 or no input
            data_image = np.asanyarray(data_frame.get_data())

        if(capture):
            capture=0
            now = datetime.datetime.now()
            p = os.path.sep.join(['./', "shot_{}.png".format(str(now).replace(":",''))])
            cv2.imwrite(p, data_image)

        if(rec):
            rec_frame = data_image
            data_image = cv2.putText(data_image,"Recording...", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,165,255),4)

        try:      
            data = cv2.imencode('.jpg', data_image)[1].tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n\r\n')
        except UnboundLocalError:
            pass

def record(out):
    global rec_frame
    while(rec):
        out.write(rec_frame)


if __name__ == '__main__':
	width = 1280
	height = 720
	fps = 30

	cfg = rs.config()
	cfg.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
	cfg.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
	cfg.enable_stream(rs.stream.infrared, 1, width, height, rs.format.y8, fps)
	cfg.enable_stream(rs.stream.infrared, 2, width, height, rs.format.y8, fps)

	pipeline = rs.pipeline()
	profile = pipeline.start(cfg)
	app.run(debug=True, use_reloader=False, use_debugger=False, host = 'localhost', port=5069, threaded=True)