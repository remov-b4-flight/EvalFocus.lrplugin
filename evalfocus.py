#!/usr/bin/python3
#Evaluate focus by OpenCV
#Author: @remov_b4_flight
import argparse
import cv2
import os
import sys
import numpy as np

#Constants
MIN_RESULT = 5
MAX_RESULT = 255

def write_image(file_path, image, sub_dir="/report", suffix=""):
    dir_file = os.path.split(file_path)
    dir = dir_file[0]
    file_name = dir_file[1]
    report_dir = dir + sub_dir

    root, ext = os.path.splitext(report_dir + "/" + file_name)
    export_file_path = root + suffix + ext

    os.makedirs(report_dir, exist_ok=True)
    cv2.imwrite(export_file_path, image)

result = 0
#Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.")
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-l", "--log", help = "save image log", action = 'store_true')
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
args = vars(ap.parse_args())

model_path = os.path.dirname(os.path.abspath(__file__))
model = os.path.join(model_path, args["model"])

if (args["v"] > 2):
    print("model=", model)

#Process Image
image_path = args["file"]

print("input image =", image_path)

original_image = cv2.imread(image_path)
if original_image is None:
    print(image_path, "CAN'T READ.")
    sys.exit(1)
image = original_image

vlog_line = 3

if (args["v"] > 2):
    print("shape =", image.shape)

#Detect front face
if (args["v"] > 2):
    print("model =", model)
fd = cv2.FaceDetectorYN_create(model, "", (0,0))
height, width, _ = image.shape
fd.setInputSize((width, height))
_, faces=fd.detect(image)
faces = faces if faces is not None else []
writeflag = False
for face in faces:
    #Report Visualization
    if ( args["log"] ):
        writeflag = True
        box = list(map(int, face[:4]))
        cv2.rectangle(image, box, (255, 0, 0), vlog_line)
    print("Score=", face[14]);

if writeflag == True:
    write_image(image_path, image)
#End of face loop
#    if (max_facelap > 0):
#        result = int(max_facelap + 0.5)

#Return value to OS
if (result > MAX_RESULT):
    result = MAX_RESULT
elif (0 < result < MIN_RESULT): 
    result = MIN_RESULT

print("result = ", result)

sys.exit(result)
