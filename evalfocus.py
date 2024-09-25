#!/opt/homebrew/bin/python3
## 
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import argparse
import cv2 as cv
import os
import sys
import numpy as np
#import matplotlib.pyplot as plt

# Constants
PIXEL10K = 10000
MIN_RESULT = 6
MAX_RESULT = 255
SMALL_LS = 2400
BIG_LS = 4800
VISUAL_WAIT = 2000
HIST_RISE = 2
POWER_RANGE = 8
MOUTH_DEDUCT = 0.75
EYE_DEDUCT = 0.85
FACE_DEDUCT = 0.95
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

#class COLOR :
#    RED = (0, 0, 255) ; BLUE = (255, 0, 0) ; GREEN = (0, 255, 0)
#    MAGENTA = (255, 0, 255) ; CYAN = (255, 255, 0) ; YELLOW = (0, 255, 255)
#    WHITE = (255, 255, 255)

# Write vlog image to home
#def write_image(file_path, image, sub_dir="vlog") :
#    homedir = os.environ['HOME']
#    (_, file_name) = os.path.split(file_path)
#    report_dir = os.path.join(homedir, sub_dir)
#    os.makedirs(report_dir, exist_ok = True)
#
#    export_file_path = os.path.join(report_dir, file_name)
#
#    cv.imwrite(export_file_path, image)

def get_resize_factor(long_side) :
    if (BIG_LS < long_side ) :
        return (1/4)
    elif (SMALL_LS < long_side <= BIG_LS) :
        return (1/2)
    else :
        return 1

def get_sobel_edges(image, ddepth, kernel) :
    sobel_x = cv.Sobel(image, ddepth, 1, 0, kernel)
    sobel_y = cv.Sobel(image, ddepth, 0, 1, kernel)
    sobel_x = cv.convertScaleAbs(sobel_x)
    sobel_y = cv.convertScaleAbs(sobel_y)
    edges = cv.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0)
    return edges

# Main
result = 0

# Option parse
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.",)
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-k", help = "laplacian kernel", type = int, choices = [1, 3, 5, 7, 9], default = 5)
ap.add_argument("-d", help = "laplacian depth", type = int, choices = [8, 32], default = 8)
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-sr", "--skip_resize", help = "skip resize", action = 'store_true', default = False)
#ap.add_argument("-g", "--graph", help = "show histgram", action = 'store_true', default = False)
#ap.add_argument("-lap", "--laplacian", help = "show laplacian", action = 'store_true', default = False)
#ap.add_argument("-vl", "--vlog", help = "save image log", action = 'store_true', default = False)

args = vars(ap.parse_args())
# Additional parameter parse
verbose = args["v"]
lap_kernel = args["k"]
match args["d"] :
    case 32 :
        lap_ddepth = cv.CV_32F
    case _ :
        lap_ddepth = cv.CV_8U

script_path = os.path.dirname(os.path.abspath(__file__))
fd_model = os.path.join(script_path, args["model"])

if (verbose >= 4) : 
    print("model =", fd_model)

image_path = args["file"]

# Model files exist check
if (os.path.isfile(fd_model) != True) :
    sys.exit(ERROR_CANTOPEN)

if (verbose >= 1) : 
    print("input image =", image_path)
# Read image
original_image = cv.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(ERROR_CANTOPEN)

# Image resizing fot face detect.
orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height,orig_width)
factor = get_resize_factor(long_side)
if (verbose >= 1) : 
    print("resize factor=", factor)
image = cv.resize(original_image, None, fx=factor, fy=factor, interpolation=cv.INTER_NEAREST_EXACT)

if (verbose >= 2) : 
    print("shape =", image.shape)

# Detecting faces.
fd = cv.FaceDetectorYN_create(fd_model, "", (0,0))
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
    1       # trusty
]]

count = 0
max_power = 0
max_index = 0

# Loop with detected faces
for face in faces :

    if (verbose >= 1) : 
        print("area", count, end=": ")
    face_rmouth_x = int(face[FACE.RMOUTH_X])
    face_lmouth_x = int(face[FACE.LMOUTH_X])
    if (faces_count >= 1 and verbose >= 2) :
        print("mouth=({0},{1})".format(face_rmouth_x, face_lmouth_x), end=", ")
    face_leye_x = int(face[FACE.LEYE_X])
    face_reye_x = int(face[FACE.REYE_X])
    if (faces_count >= 1 and verbose >= 2) :
        print("eye=({0},{1})".format(face_reye_x, face_leye_x), end=", ")
    face_trusty = round(face[FACE.TRUSTY], 2) if faces_count >= 1 else 0.0
    # Crop face
    face_x1 = int(face[FACE.X])
    face_x2 = int(face[FACE.X] + face[FACE.WIDTH])
    face_y1 = int(face[FACE.Y])
    face_y2 = int(face[FACE.Y] + face[FACE.HEIGHT])
    face_image = image[face_y1 : face_y2,
                        face_x1 : face_x2]
    # Grayscale conversion
    gray = cv.cvtColor(face_image, cv.COLOR_BGR2GRAY)
    if (faces_count == 0) : 
        # Sobel filter
        edge_image = get_sobel_edges(gray, lap_ddepth, lap_kernel)
    else :
        # Laplacian conversion
        edge_image = cv.Laplacian(gray, lap_ddepth, lap_kernel)

    #if (args["laplacian"] and (faces_count >= 1 or verbose >= 3)) :
    #       cv.imshow("Cropped", edge_image)
    #       cv.waitKey(VISUAL_WAIT)

    # Get result
    hist, bins = np.histogram(edge_image, bins = 32, range = (0,255))
    power_length = len(hist)

    # Determine power calc. start/end
    power_start = 0
    power_end = 0

    for i in range((power_length - 1), 0, -1) :
        if (power_end == 0 and hist[i] != 0) :
            power_end = i
        else  :
            if (power_end != 0 and hist[i] != 0 and (hist[i - 1] / hist[i]) > HIST_RISE) :
                power_start = i
    # Limit power_start 
    if (power_start == 0 or (power_end - power_start) > POWER_RANGE ) :
        power_start = power_end - POWER_RANGE + 1

    if (verbose >= 4) :
        print()
        print("hist=", hist)
    if (verbose >= 3) : 
        print("power_start=", power_start, end=", ")
        print("power_end=", power_end)
        print("hist=", hist[ power_start : power_end + 1], end=", ")

    # Calc. the power
    power = 0
    for i in range(power_start, power_end + 1) :
        power += hist[i] * i

    if (verbose >= 1) : 
        print("power=", power, end=", ")

    # If no faces not detected results deducted.
    if (faces_count != 0) : 
        if (face_rmouth_x <= 0 and face_lmouth_x <= 0) : 
            power *= MOUTH_DEDUCT
        if (face_reye_x <= 0 and face_leye_x <= 0) : 
            power *= EYE_DEDUCT

    power = int(power)

    if (verbose >= 1 and faces_count >= 1) : 
        print("trusty=", face_trusty, end=", ")
    if (power > max_power) : 
        max_power = power
        max_index = count
    if (verbose >= 1) : print()

    count += 1
# End loop of faces

max_face = faces[max_index]
if (verbose >= 3) : 
    print("width=", max_face[FACE.WIDTH])
    print("height=", max_face[FACE.HEIGHT])
pixel_count = max_face[FACE.WIDTH] * max_face[FACE.HEIGHT] // PIXEL10K

#round up for too small face
if (pixel_count == 0) :
    pixel_count = 1

power_kpixel = max_power / pixel_count
if (verbose >= 2) :
    print("10Kpixels=", pixel_count)
    print("power/10Kpixels={0:.2f}".format(power_kpixel))
result = int(np.ceil(power_kpixel))

# Make image log
#if (args["vlog"]) :
#    # Draw result for face has max power
#    if(faces_count >= 1) :
#        vlog_line = max(width,height) // 1000
#        if (vlog_line < 3) : vlog_line = 3

#        box = list(map(int, max_face[:4]))
#        max_x = int(max_face[FACE.X])
#        max_y = int(max_face[FACE.Y])
#        max_rmouth_x = int(max_face[FACE.RMOUTH_X])
#        max_rmouth_y = int(max_face[FACE.RMOUTH_Y])
#        max_lmouth_x = int(max_face[FACE.LMOUTH_X])
#        max_lmouth_y = int(max_face[FACE.LMOUTH_Y])

#        cv.rectangle(image, box, COLOR.BLUE, vlog_line)
#        cv.putText(image, str(face_trusty), (max_x, (max_y - 8)), 
#                    cv.FONT_HERSHEY_DUPLEX, 0.8, COLOR.CYAN, 3)
#        cv.circle(image, [max_rmouth_x, max_rmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
#        cv.circle(image, [max_lmouth_x, max_lmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
#    # Draw total result
#    cv.putText(image, ("Result=" + str(result)), (32, 64), 
#                cv.FONT_HERSHEY_SIMPLEX, 2.0, COLOR.RED, 6)
#    write_image(image_path, image)

# Show histgram
#if (args['graph']) :
#    (_, base_name) = os.path.split(image_path)
#    hist_title = str(max_power) + ' / ' + base_name
#    plt.stairs(hist, bins, fill = True)
#    plt.title(hist_title)
#    plt.show()

# Return value to OS
if (result > MAX_RESULT) :
    result = MAX_RESULT
elif (0 <= result < MIN_RESULT) : 
    result = MIN_RESULT

print("result=", result)
sys.exit(result)
