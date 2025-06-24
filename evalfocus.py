#!/opt/homebrew/bin/python3
## 
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import argparse
import cv2 as cv
import os
import sys
import numpy as np
#import threading as th

# Constants
PIXEL10K = 10000
# Ignore smaller face than this factor by entire of image.
IGNORE_FACE_FACTOR = (0.075 / 100) # 0.075%
# Constants for result range
MIN_RESULT = 5
MAX_RESULT = 255
# Constants for resize 
SMALL_LONGSIDE = 2000
BIG_LONGSIDE = 4000
# User interface
VISUAL_WAIT = 1000  # 1 sec
# Constants for face recognition 
SCORE_THRESHOLD = 0.75
# Constants for power estimation
HIST_BINS = 32
MAX_BINS = (HIST_BINS - 1)
POWER_END_GATE = ((HIST_BINS // 8) * 3)
POWER_END_DESCEND = ((HIST_BINS // 8) * 6)
HIST_RISE = 2
POWER_RANGE = 6
# Constants for power deduction
MOUTH_DEDUCT = 0.8
EYE_DEDUCT = 0.75
NOSE_DEDUCT = 0.85
# Constants for power pole
POWER_CLIFF = 0.9
POWER_SLOPE = 0.066
# Mask area for foulier transform 
FOULIER_MASK = 8
# Tolerance for canny filter
SIGMA = 0.33
# Error code for OS
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
    SCORE = 14

# Color constants for visual log
class COLOR :
    RED = (0, 0, 255) ; BLUE = (255, 0, 0) ; GREEN = (0, 255, 0)
    MAGENTA = (255, 0, 255) ; CYAN = (255, 255, 0) ; YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)

# Write visual log image to home folder.
def write_image(file_path, image, sub_dir="vlog") :
    homedir = os.environ['HOME']
    (_, file_name) = os.path.split(file_path)
    report_dir = os.path.join(homedir, sub_dir)
    os.makedirs(report_dir, exist_ok = True)
    export_file_path = os.path.join(report_dir, file_name)
    cv.imwrite(export_file_path, image)

# Get resize factor from long side of image.
def get_resize_factor(long_side) :
    if (BIG_LONGSIDE < long_side) :
        return (1/4)
    elif (SMALL_LONGSIDE < long_side <= BIG_LONGSIDE) :
        return (1/2)
    else :
        return 1

# Detecting images edges using Sobel filter.
def get_sobel_edges(image, ddepth, kernel) :
    sobel_x = cv.convertScaleAbs(cv.Sobel(image, ddepth, 1, 0, kernel))
    sobel_y = cv.convertScaleAbs(cv.Sobel(image, ddepth, 0, 1, kernel))
    edges = cv.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0)
    return edges

# Detecting image edges using Canny filter.
def get_canny_edges(image, sigma) :
    median_value = np.median(image)
    min_value = int( max(0, (1.0-sigma) * median_value) )
    max_value = int( max(255, (1.0+sigma) * median_value) )
    edges = cv.Canny(image, min_value, max_value)
    return edges

# Metering image power using foulier transform.
def get_foulier_power(image) :
    f = np.fft.fft2(image)
    fshift = np.fft.fftshift(f)
    mag = 20 * np.log(np.abs(fshift))
    mw, mh = mag.shape
    mcx = mw // 2
    mcy = mh // 2
    fx = mcx // FOULIER_MASK
    fy = mcy // FOULIER_MASK
    #mask low frequency area
    mag[0+fx : mw-fx, mcy-fy : mcy+fy] = 0
    mag[mcx-fx : mcx+fx, 0+fy : mh-fy] = 0 
    return np.sum(mag)

# Main

# Parseing Options.
ap = argparse.ArgumentParser(description = "Evaluate image focus.")
ap.add_argument("file", help = "Image file to process.",)
ap.add_argument("-v", help = "verbose outputs", action = 'count', default = 0)
ap.add_argument("-k", help = "filter kernel", type = int, choices = [1, 3, 5, 7, 9], default = 5)
ap.add_argument("-d", help = "filter depth", type = int, choices = [8, 32], default = 8)
ap.add_argument("-so", "--sobel", help = "force sobel", action = 'store_true', default = False)
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-g", "--graph", help = "show histgram", action = 'store_true', default = False)
ap.add_argument("-eg", "--edge", help = "show edges", action = 'store_true', default = False)
ap.add_argument("-nm", "--normalize", help = "normalize", action = 'store_true', default = False)
ap.add_argument("-vl", "--vlog", help = "save visual log", action = 'store_true', default = False)

args = vars(ap.parse_args())

# Parseing additional parameters.
verbose = args["v"]
filter_kernel = args["k"]
filter_ddepth = cv.CV_32F if (args["d"] == 32) else cv.CV_8U 

script_path = os.path.dirname(os.path.abspath(__file__))
fd_model = os.path.join(script_path, args["model"])

if (verbose >= 5) : 
    print("model=", fd_model)

image_path = args["file"]

# Exists check for Model file.
if (os.path.isfile(fd_model) != True) :
    sys.exit(ERROR_CANTOPEN)

if (verbose >= 1) : 
    print("input image=", image_path)
# Input image exist check.
if (os.path.isfile(image_path) != True) :
    print(image_path, " NOT EXISTS.")
    sys.exit(ERROR_CANTOPEN)
# Read image.
original_image = cv.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(ERROR_CANTOPEN)

if (verbose >= 2) : 
    print("original size=",original_image.shape)

# Image resizing fot face detect.
orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height, orig_width)
factor = get_resize_factor(long_side)
if (verbose >= 2) : 
    print("resize factor=", factor)

image = cv.resize(original_image, None, fx=factor, fy=factor, 
                    interpolation=cv.INTER_NEAREST_EXACT)

# Normalize image if option is set.
if (args["normalize"]) :
    image = cv.normalize(image, None, 0, 255, cv.NORM_MINMAX)

if (verbose >= 2) : 
    print("resized image=", image.shape)

# Detecting faces.
resized_height, resized_width, _ = image.shape
resized_pixels = resized_height * resized_width
fd = cv.FaceDetectorYN_create(fd_model, "", (resized_width, resized_height), SCORE_THRESHOLD)
_, faces = fd.detect(image)

faces_count = len(faces) if faces is not None else 0
if (verbose >= 1) : 
    print("faces=", faces_count)

# If any face not found, process entire of image.
faces = faces if faces is not None else [[
    0, 0, resized_width, resized_height, 
    0, 0,   # right eye (x,y)
    0, 0,   # left eye (x,y)
    0, 0,   # nose (x,y)
    -1, -1,   # right mouth edge (x,y)
    -1, -1,   # left mouth edge (x,y)
    1       # trusty
]]

count = 0
max_power = -1
max_index = -1
max_foulier = -1

# Iterate loop with detected faces.
for img_it in faces :

    if (verbose >= 1) : 
        print("area", count, end=": ")

    face_width = int(img_it[FACE.WIDTH])
    face_height = int(img_it[FACE.HEIGHT])
    if (verbose >= 2) :
        print("width={0}, height={1}".format(face_width, face_height), end=", ")

    # If face size is too small, skip it.
    face_pixels = face_width * face_height
    if ((face_pixels / resized_pixels) < IGNORE_FACE_FACTOR) :
        print("It's too small face, skipped.")
        count += 1
        continue

    # Get mouth detecting result
    face_rmouth_x = int(img_it[FACE.RMOUTH_X])
    face_lmouth_x = int(img_it[FACE.LMOUTH_X])
    if (faces_count >= 1 and verbose >= 3) :
        print("mouth=({0},{1})".format(face_rmouth_x, face_lmouth_x), end=", ")

    # Get eye detecting result
    face_leye_x = int(img_it[FACE.LEYE_X])
    face_reye_x = int(img_it[FACE.REYE_X])
    if (faces_count >= 1 and verbose >= 3) :
        print("eye=({0},{1})".format(face_reye_x, face_leye_x), end=", ")

    # Get nose detecting result
    face_nose_x = int(img_it[FACE.NOSE_X])
    face_nose_y = int(img_it[FACE.NOSE_Y])
    if (faces_count >= 1 and verbose >= 3) :
        print("nose=({0},{1})".format(face_nose_x, face_nose_y), end=", ")

    # Get face detecting result
    face_score = round(img_it[FACE.SCORE], 2) if faces_count >= 1 else 0.0
    # Crop face
    img_x1 = 0 if (img_it[FACE.X] < 0) else int(img_it[FACE.X]) 
    img_x2 = img_x1 + int(img_it[FACE.WIDTH])
    img_y1 = 0 if (img_it[FACE.Y] < 0) else int(img_it[FACE.Y])
    img_y2 = img_y1 + int(img_it[FACE.HEIGHT])
    crop_image = image[img_y1 : img_y2, img_x1 : img_x2]
    if (verbose >= 5) :
        print ("image x1={0},x2={1},y1={2},y2={3}".format(img_x1,img_x2,img_y1,img_y2))

    # Grayscale conversion.
    gray_image = cv.cvtColor(crop_image, cv.COLOR_BGR2GRAY)

    # Make edge image
    if (args["sobel"]) : 
        # Sobel filter
        edge_image = get_sobel_edges(gray_image, filter_ddepth, filter_kernel)
    else :
        # Laplacian conversion
        edge_image = cv.Laplacian(gray_image, filter_ddepth, filter_kernel)

    # Show edge image by option.
    if (args["edge"]) :
           cv.imshow("Edges", edge_image)
           cv.waitKey(VISUAL_WAIT)

    # Get histogram from edge image.
    hist, bins = np.histogram(edge_image, bins = HIST_BINS, range = (0,255))
    power_length = len(hist)

    # Determine start/end for power calculation.
    power_start = 0
    power_end = 0
    # Seeking power_start and power_end.
    for i in range((power_length - 1), 0, -1) :
        # Find first point of hist[] not zero
        if (power_end == 0 and hist[i] != 0) :
            power_end = i
        # Find hist[] rising point        
        elif (power_end != 0 and hist[i] != 0 and (hist[i + 1] / hist[i]) > HIST_RISE) :
                power_start = i
    # Limit power_start by POWER_RANGE.
    if (power_start == 0 or (power_end - power_start) > POWER_RANGE ) :
        power_start = power_end - POWER_RANGE + 1

    if (verbose >= 3) : 
        print("power_start=", power_start, end=", ")
        print("power_end=", power_end, end=", ")
        if (verbose >= 4) :
            print()
            print("hist=", hist)
        else : 
            print("hist=", hist[ power_start : power_end + 1], end=", ")

    # Calculate power of current face.
    power = 0
    for i in range(power_start, power_end + 1) :
        power += hist[i] * i
    # Power deducted by dispartion of histgrom
    if (power_end == MAX_BINS) :
        power *= 1.25
    else : 
        if (power_end == (MAX_BINS - 1)) :
            power *= 1.1
        if (POWER_END_GATE < power_end < POWER_END_DESCEND) : 
            power *= 0.75
    # Power deducted by face detection result
    if (faces_count != 0) : 
        if (face_rmouth_x <= 0 and face_lmouth_x <= 0) : 
            power *= MOUTH_DEDUCT
        if (face_reye_x <= 0 and face_leye_x <= 0) : 
            power *= EYE_DEDUCT
        if (face_nose_x <= 0 and face_nose_y <= 0) :
            power *= NOSE_DEDUCT
    if (verbose >= 1) : 
        print("power=", power, end=", ")

    if (verbose >= 1 and faces_count >= 1) : 
        print("score=", face_score, end=", ")
    # Flashing max_power
    if (power > max_power and power_end > POWER_END_GATE) : 
        max_power = power
        max_index = count
    if (verbose >= 1) : 
        print()

    count += 1
# End iteration of faces.

# Evaluate face has max_power.
if (max_power < 0) :
    #It seems no face through POWER_GATE in image or too small face.
    result = 0
    faces_count = 0
else :
    max_face = faces[max_index]
    max_width = int(max_face[FACE.WIDTH])
    max_height = int(max_face[FACE.HEIGHT])
    max_score = max_face[FACE.SCORE]

    # Make slope for image(face) has low score.
    max_power *= ((max_score + POWER_SLOPE) ** 2) if (max_score < POWER_CLIFF) else max_score

    if (verbose >= 3) : 
        print("max width={0}, height={1}".format(max_width, max_height))
    # if face count is 0, use half of image size as ROI.
    if (faces_count == 0) :
        max_width /= 2
        max_height /= 2

    pixel_count = int(max_width * max_height / PIXEL10K)

    # Rounds up for too small face.
    if (pixel_count < 1) :
        pixel_count = 1
    # Make result.
    power_kpixel = max_power / pixel_count
    result = round(power_kpixel)
    if (verbose >= 2) :
        print("10Kpixels=", pixel_count)
        print("max power=", max_power)
        print("power/10Kpixels=", power_kpixel)

# Output result to stdout.
if (verbose >= 1) : 
    print("result=", result)

# Make 'visual log' by option.
if (args["vlog"]) :
    # Draw result for face has max power
    if(faces_count >= 1) :
        vlog_line = max(resized_width, resized_height) // 1000
        if (vlog_line < 3) : vlog_line = 3

        box = list(map(int, max_face[:4]))
        max_x = int(max_face[FACE.X])
        max_y = int(max_face[FACE.Y])
        max_rmouth_x = int(max_face[FACE.RMOUTH_X])
        max_rmouth_y = int(max_face[FACE.RMOUTH_Y])
        max_lmouth_x = int(max_face[FACE.LMOUTH_X])
        max_lmouth_y = int(max_face[FACE.LMOUTH_Y])

        cv.rectangle(image, box, COLOR.BLUE, vlog_line)
        cv.putText(image, str(face_score), (max_x, (max_y - 8)), 
                    cv.FONT_HERSHEY_DUPLEX, 0.8, COLOR.CYAN, 3)
        cv.circle(image, [max_rmouth_x, max_rmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
        cv.circle(image, [max_lmouth_x, max_lmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
        cv.circle(image, [int(max_face[FACE.REYE_X]), int(max_face[FACE.REYE_Y])], 5, COLOR.RED, -1, cv.LINE_AA)
        cv.circle(image, [int(max_face[FACE.LEYE_X]), int(max_face[FACE.LEYE_Y])], 5, COLOR.RED, -1, cv.LINE_AA)
        cv.circle(image, [int(max_face[FACE.NOSE_X]), int(max_face[FACE.NOSE_Y])], 5, COLOR.GREEN, -1, cv.LINE_AA)
    # Draw total result
    cv.putText(image, ("Result=" + str(result)), (32, 64), 
                cv.FONT_HERSHEY_SIMPLEX, 2.0, COLOR.RED, 6)
    write_image(image_path, image)

# Show histgram
if (args['graph'] == True) :
    import matplotlib.pyplot as plt
    (_, base_name) = os.path.split(image_path)
    hist_title = str(max_power) + ' / ' + base_name
    plt.stairs(hist, bins, fill = True)
    plt.title(hist_title)
    plt.show()

# Return value to OS
if (result > MAX_RESULT) :
    result = MAX_RESULT
elif (0 <= result < MIN_RESULT) : 
    result = MIN_RESULT
sys.exit(result)