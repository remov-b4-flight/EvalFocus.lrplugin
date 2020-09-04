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

def crop_faces(gray, faces):
    return [gray[y: y + h, x: x + w] for x,y,w,h in faces]

def resize_image(image):
    height, width = image.shape[:2]
    while width >= 1500:
        image = resize_image_to_harf(image)
        height, width = image.shape[:2]
    else:
        return image

def resize_image_to_harf(image):
    return cv2.resize(image,None,fx=0.5, fy=0.5)

#Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.")
ap.add_argument("-v", help = "verbose outputs", action='count', default = 0)
ap.add_argument("-l", help = "save image log", action='store_true')
ap.add_argument("-c", "--cascade", help = "cascade file", default = "haarcascade_frontalface_default.xml")
ap.add_argument("-p", "--profile", help = "profile file", default = "haarcascade_profileface.xml")
ap.add_argument("-e", "--eye", help = "eye cascade file", default = "haarcascade_eye.xml")
ap.add_argument("-s", "--scale", help = "scale factor", type = float, default = 1.08)
ap.add_argument("-n", "--neighbor", help = "minNeighbor param", type = int, default = 3)
args = vars(ap.parse_args())

cascade_path = os.path.dirname(os.path.abspath(__file__))
cascade_file_front = os.path.join(cascade_path, args["cascade"])
cascade_file_prof = os.path.join(cascade_path, args["profile"])
cascade_file_eye = os.path.join(cascade_path, args["eye"])

if (args["v"] > 1):
    print("cascade front=", cascade_file_front)
    print("cascade profile=", cascade_file_prof)
    print("cascade eye=", cascade_file_eye)

#Process Image
image_path = args["file"]

if (args["v"] > 0):
    print("--------")
    print("input image =", image_path)

original_image = cv2.imread(image_path)
if original_image is None:
    print(image_path, "CAN'T READ.")
    sys.exit(1)

#image = original_image
image = resize_image(original_image)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
longside = max(image.shape[0],image.shape[1])
minsize = int(longside / 10)
maxsize = int(longside / 1.5)

if (args["v"] > 1):
    print("shape =", image.shape)
    print("scale =",args["scale"])
    print("neighbor =",args["neighbor"])
    print("minsize =", minsize)
    print("maxsize =", maxsize)

#Detect front face
front_cascade = cv2.CascadeClassifier(cascade_file_front)
front_faces = front_cascade.detectMultiScale( gray, 
scaleFactor = args["scale"], 
minNeighbors = args["neighbor"], 
minSize = (minsize, minsize),
maxSize = (maxsize, maxsize) )
if len(front_faces) and (args["v"] > 1):
    print("front faces = ", front_faces)

#Detect profile face
profile_cascade = cv2.CascadeClassifier(cascade_file_prof)
profile_faces = profile_cascade.detectMultiScale( gray, 
scaleFactor = args["scale"], 
minNeighbors = args["neighbor"], 
minSize = (minsize, minsize),
maxSize = (maxsize, maxsize) )
if len(profile_faces) and (args["v"] > 1):
    print("profile faces = ", profile_faces)

#Joint front & profile
if len(front_faces) and len(profile_faces):
    faces = np.vstack([front_faces, profile_faces])
elif len(front_faces) and (len(profile_faces) == 0):
    faces = front_faces.copy()
elif (len(front_faces) == 0) and len(profile_faces):
    faces = profile_faces.copy()
else:
    faces = np.empty([0,0,0,0])

if (args["v"] > 1):
    print("faces = ", faces)

face_laplacians = None
if len(faces):
    face_images = crop_faces(gray, faces)
    face_laplacians = [cv2.Laplacian(face_image, cv2.CV_64F) for face_image in face_images]

laplacian = cv2.Laplacian(gray, cv2.CV_64F)
#Report about image
print( '%d %3.2f %d %d' % (0, laplacian.var(), gray.shape[0], gray.shape[1]) ) 

#Any faces is there
if len(faces):
    print("faces = ", len(faces))
    eye_cascade = cv2.CascadeClassifier(cascade_file_eye)
    max_facelap = 0
    #Face loop
    for index,(x, y, w, h) in enumerate(faces):
        facelap = face_laplacians[index].var()
        if facelap > max_facelap:
            max_facelap = facelap
        print( '%d %3.2f %d %d' % (index + 1, facelap, w, h), end=" " )

        longeye = max(w,h)
        mineye = int(longeye / 16)
        maxeye = int(longeye / 4)
        eyes = eye_cascade.detectMultiScale( face_images[index],
        scaleFactor = args["scale"], 
        minNeighbors = args["neighbor"], 
        minSize = (mineye, mineye),
        maxSize = (maxeye, maxeye) )        
        if len(eyes):
            print("eyes = ", len(eyes))
        else:
            max_facelap = 0 #determine this area has no face.
            print(" ")

        #Report Visualization
        if (args["l"]):
            cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(image, "{}: {:.2f} {}:{:2d}".format( "Face", face_laplacians[index].var(), "eyes", len(eyes) ), (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
            cv2.putText(image, "{}: {:.2f}".format("Image",laplacian.var()), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
            write_image(image_path, image)
    #End of face loop
    if (max_facelap > 0):
        result = int(max_facelap)
    else:
        result = 0
#Faces not detected
else:
    result = int(laplacian.var())
#Return value to OS
if (result > MAX_RESULT):
    result = MAX_RESULT
elif (0 < result < MIN_RESULT): 
    result = MIN_RESULT

if (args["v"] > 0):
    print("result = ",result)

sys.exit(result)
