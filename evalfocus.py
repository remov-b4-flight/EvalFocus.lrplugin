#!/usr/bin/python3
#Evaluate focus by OpenCV
#Author: @remov_b4_flight
import argparse
import cv2
import os
import sys

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

if (args["v"] > 2) : print("model=", model)

image_path = args["file"]

if (args["v"] > 1) : print("input image =", image_path)

#Read image
original_image = cv2.imread(image_path)
if original_image is None:
    print(image_path, "CAN'T READ.")
    sys.exit(1)
image = original_image

if (args["v"] > 2) : print("shape =", image.shape)

#Detect front face
if (args["v"] > 3):
    print("model =", model)

fd = cv2.FaceDetectorYN_create(model, "", (0,0))
height, width, _ = image.shape
fd.setInputSize((width, height))
_, faces=fd.detect(image)

if (args["v"] > 1):
    print("faces =", len(faces) if faces is not None else 0)
#If any face not found, process entire image.
faces = faces if faces is not None else [[0,0,width,height]]

vlog_line = int(max(width,height) / 1000)
if (vlog_line < 3) : vlog_line = 3
writeflag = False
count = 0
max_result = 0
#Loop with detected faces
for face in faces:
    print("area ", count,end="")
    #Crop face
    face_image = image[ int(face[1]):int(face[1]+face[3]),
                        int(face[0]):int(face[0]+face[2])]
    #Gray convert
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    #Laplacian convert
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    if (args["v"] > 2):
        cv2.imshow("crop",laplacian)
        cv2.waitKey(1000)
    #Get result
    result = int(laplacian.var() + 0.5)
    print(" result =", result,end="")

    #Report Visualization
    if ( args["log"] ):
        writeflag = True
        box = list(map(int, face[:4]))
        cv2.rectangle(image, box, (255, 0, 0), vlog_line)
    if (args["v"] > 1) : print(" Score =", face[-1],end="")
    #End of loop
    count += 1
    if (result > max_result) : max_result = result
    print()
#End loop of faces
if (writeflag == True) : write_image(image_path, image)

#Return value to OS
if (max_result > MAX_RESULT):
    max_result = MAX_RESULT
elif (0 < max_result < MIN_RESULT): 
    max_result = MIN_RESULT

print("result = ", max_result)
sys.exit(result)
