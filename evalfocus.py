#!/opt/homebrew/bin/python3
## 
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import argparse
import cv2
import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt

# Constants
MIN_RESULT = 5
MAX_RESULT = 255
SMALL_LS = 2400
BIG_LS = 4800
VISUAL_WAIT = 2000
POWER_RANGE = 8
MOUTH_DEDUCT = 0.75
FACE_DEDUCT = 0.9
# Error code
ERROR_CANTOPEN = 2
# FaceDetectorYN result index
class FACE :
    X = 0 ; Y = 1
    WIDTH = 2 ; HEIGHT = 3
    REYE_X = 4 ; REYE_Y = 5
    LEYE_X = 6 ; LEYE_Y = 7
    NOSE_X = 8 ; NOSE_Y = 9
    RMOUTH_X = 10 ; RMOUTH_Y = 11
    LMOUTH_X = 12 ; LMOUTH_Y = 13
    TRUSTY = 14

# Write vlog image to home
def write_image(file_path, image, sub_dir="vlog") :
    homedir = os.environ['HOME']
    (_, file_name) = os.path.split(file_path)
    report_dir = os.path.join(homedir, sub_dir)
    os.makedirs(report_dir, exist_ok=True)

    export_file_path = os.path.join(report_dir,file_name)

    cv2.imwrite(export_file_path, image)

# get 1/(2^n) long side size for image
def adjust_long(long_side) :
    if (BIG_LS < long_side ) :
        long_result = int(long_side / 4)
    elif (SMALL_LS < long_side <= BIG_LS) :
        long_result = int(long_side / 2)
    else :
        long_result = -1
 
    return long_result

# Main
result = 0

# Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.")
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-k", help = "laplacian kernel", type = int, default = 5)
ap.add_argument("-g", "--graph", help = "show histgram", action = 'store_true', default = False)
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-bm", "--brisque_model", help = "BRISQUE model file", default = "brisque_model_live.yml")
ap.add_argument("-br", "--brisque_range", help = "BRISQUE range file", default = "brisque_range_live.yml")
ap.add_argument("-sr", "--skip_resize", help = "skip resize", action = 'store_true', default = False)
ap.add_argument("-sb", "--skip_brisque", help = "skip brisque", action = 'store_true', default = False)
ap.add_argument("-lap", "--laplacian", help = "show laplacian", action = 'store_true', default = False)
ap.add_argument("-vl", "--vlog", help = "save image log", action = 'store_true', default = False)

args = vars(ap.parse_args())

verbose = args["v"]
lap_kernel = args["k"]

script_path = os.path.dirname(os.path.abspath(__file__))
fd_model = os.path.join(script_path, args["model"])

brisque_model = os.path.join(script_path, args["brisque_model"])
brisque_range = os.path.join(script_path, args["brisque_range"])

if (verbose >= 4) : 
    print("model =", fd_model)
    print("brisque_model =", brisque_model)
    print("brisque_range =", brisque_range)

image_path = args["file"]

if (os.path.isfile(fd_model) != True) :
    sys.exit(ERROR_CANTOPEN)
if (os.path.isfile(brisque_model) != True) :
    skip_brisque = True
if (os.path.isfile(brisque_model) != True) :
    skip_brisque = True

if (verbose >= 1) : 
    print("input image =", image_path)
# Read image
original_image = cv2.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(ERROR_CANTOPEN)

if (args["skip_brisque"] != True) :
    # BRISQUE evaluation
    brisque_array = cv2.quality.QualityBRISQUE_compute(original_image, brisque_model, brisque_range)
    brisque_score = round(brisque_array[0], 2)
    if (verbose >= 1) : print("BRISQUE score =", brisque_score)
    if (brisque_score > 80.0) :
        if (verbose >= 2) : 
            print("Evaluate terminated by low BRISQUE score.")
        sys.exit(MIN_RESULT)

orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height,orig_width)
resize_long = adjust_long(long_side)
if (resize_long < 0 or args["skip_resize"] == True) : # No resize
    image = original_image
else :
    aspect = orig_width / orig_height
    if (orig_height >= orig_width) : #portlait
        target_size = (int(resize_long * aspect), resize_long)
    else : #landscape
        target_size = (resize_long, int(resize_long / aspect))
    image = cv2.resize(original_image,target_size, interpolation = cv2.INTER_NEAREST_EXACT)

if (verbose >= 2) : 
    print("shape =", image.shape)

# Detect faces
fd = cv2.FaceDetectorYN_create(fd_model, "", (0,0))
height, width, _ = image.shape
fd.setInputSize((width, height))
_, faces = fd.detect(image)

faces_count = len(faces) if faces is not None else 0
if (verbose >= 1) : 
    print("faces =", faces_count)

# If any face not found, process entire image.
faces = faces if faces is not None else [[
    0, 0, width, height, 
    0, 0,   # right eye (x,y)
    0, 0,   # left eye (x,y)
    0, 0,   # nose (x,y)
    -1, -1,   # right mouth edge (x,y)
    -1, -1,   # left mouth edge (x,y)
    -1
]]

count = 0
max_power = 0
max_index = 0

# Loop with detected faces
for face in faces :

    if (verbose >= 1) : 
        print("area", count, end=": ")
    face_rmouth_x = int(face[FACE.RMOUTH_X])
#   face_rmouth_y = int(face[FACE.RMOUTH_Y])
    face_lmouth_x = int(face[FACE.LMOUTH_X])
#   face_lmouth_y = int(face[FACE.LMOUTH_Y])
    if (faces_count >= 1 and verbose >= 2) :
        print("mouth=({0},{1})".format(face_rmouth_x, face_lmouth_x), end=", ")
    face_trusty = round(face[FACE.TRUSTY], 2) if faces_count >= 1 else 0.0
    #Crop face
    face_x1 = int(face[FACE.X])
    face_x2 = int(face[FACE.X] + face[FACE.WIDTH])
    face_y1 = int(face[FACE.Y])
    face_y2 = int(face[FACE.Y] + face[FACE.HEIGHT])
    face_image = image[face_y1 : face_y2,
                        face_x1 : face_x2]
    #Grayscale conversion
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    #Laplacian conversion
    laplacian = cv2.Laplacian(gray, cv2.CV_8U, lap_kernel)
    if (args["laplacian"] and (faces_count >= 1 or verbose >= 3)) :
        cv2.imshow("crop", laplacian)
        cv2.waitKey(VISUAL_WAIT)
    # Get result
    hist, bins = np.histogram(laplacian, bins = 32, range = (0,255))
    # Compute the power
    power = 0
    power_length = len(hist)
    power_start = int(power_length - POWER_RANGE)
    if (verbose >= 3) : 
        print("hist=", hist[ -1 * POWER_RANGE : ], end=", ")
    for i in range(power_start, power_length) :
        power += hist[i] * i

    if (verbose >= 1) : 
        print("power=", power,end=", ")
    
    # If no faces not detected results deducted.
    if (faces_count == 0) : 
        power *= FACE_DEDUCT
    # If both mouth edge not detected, results deducted.
    elif (face_rmouth_x <= 0 and face_lmouth_x <= 0) : power *= MOUTH_DEDUCT

    power = int(power)

    if (verbose >= 1 and faces_count >= 1) : 
        print("trusty=", face_trusty, end=", ")
    if (power > max_power) : 
        max_power = power
        max_index = count
    if (verbose >= 1) : print()
    # End of loop
    count += 1
# End loop of faces

max_face = faces[max_index]
pixel_count = int(max_face[FACE.WIDTH] * max_face[FACE.HEIGHT] / 10000)
power_kpixel = math.ceil(max_power / pixel_count)
if (verbose >= 2) :
    print("10Kpixels=", pixel_count)
    print("power/10Kpixels=", power_kpixel)
result = power_kpixel

# Make image log
if (args["vlog"]) :
    vlog_line = int(max(width,height) / 1000)
    if (vlog_line < 3) : vlog_line = 3
    box = list(map(int, max_face[:4]))
    max_x = int(max_face[FACE.X])
    max_y = int(max_face[FACE.Y])
    max_rmouth_x = int(max_face[FACE.RMOUTH_X])
    max_rmouth_y = int(max_face[FACE.RMOUTH_Y])
    max_lmouth_x = int(max_face[FACE.LMOUTH_X])
    max_lmouth_y = int(max_face[FACE.LMOUTH_Y])

    cv2.rectangle(image, box, (255, 0, 0), vlog_line)
    cv2.putText(image, str(face_trusty), (max_x, (max_y - 8)), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,0), 3)
    cv2.putText(image, ("Result=" + str(result)), (32, 64), 
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 192), 6)
    cv2.circle(image, [max_rmouth_x, max_rmouth_y], 5, (255,0,255), -1, cv2.LINE_AA)
    cv2.circle(image, [max_lmouth_x, max_lmouth_y], 5, (255,0,255), -1, cv2.LINE_AA)
    write_image(image_path, image)

# Show histgram
if (args['graph']) :
    (_, base_name) = os.path.split(image_path)
    hist_title = str(max_power) + ' / ' + base_name
    plt.stairs(hist, bins, fill = True)
    plt.title(hist_title)
    plt.show()

# Return value to OS
if (result > MAX_RESULT) :
    result = MAX_RESULT
elif (0 < result < MIN_RESULT) : 
    result = MIN_RESULT

print("result=", result)
sys.exit(result)
