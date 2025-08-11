#!/opt/homebrew/bin/python3
""" Evaluate focus by OpenCV functions. """
# @file evalfocus.py
# @brief Evaluate focus by OpenCV functions.
# @author remov_b4_flight

import sys
import os
import time
import argparse
import cv2 as cv
import numpy as np

# Constants
PIXEL10K = 10000
# Normalize image if stddev < this value.
NORMALIZE_THRESHOLD = 50.0
# Ignore smaller face than this factor by entire of image.
IGNORE_FACE_FACTOR = 0.075 / 100 # 0.075%
# Constants for result range
MIN_RESULT = 5
MAX_RESULT = 255
# Constants for resize
SMALL_LONGSIDE = 2000
BIG_LONGSIDE = 4000
# Constants for face detection
SCORE_THRESHOLD = 0.75
TOP_K = 25
# Constants for power estimation
HIST_BINS = 32
MAX_BIN_INDEX = HIST_BINS - 1
POWER_END_GATE = (HIST_BINS // 8) * 3
POWER_END_DESCEND = (HIST_BINS // 8) * 6
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
# Vlog constants
IMPOSE_OFFSET = 16
PLOT_DPI = 80

# FaceDetectorYN result index
class FACE :
    """ FaceDetectorYN result index """
    X = 0
    Y = 1
    WIDTH = 2
    HEIGHT = 3
    REYE_X = 4
    REYE_Y = 5
    LEYE_X = 6
    LEYE_Y = 7
    NOSE_X = 8
    NOSE_Y = 9
    RMOUTH_X = 10
    RMOUTH_Y = 11
    LMOUTH_X = 12
    LMOUTH_Y = 13
    SCORE = 14

# Color constants for visual log
class COLOR :
    """ Color constants for visual log """
    RED = (0, 0, 255)
    BLUE = (255, 0, 0)
    GREEN = (0, 255, 0)
    MAGENTA = (255, 0, 255)
    CYAN = (255, 255, 0)
    YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)
    MID_YELLOW = (0, 192, 192)

class NORMALIZE :
    """ Normalization modes for image processing """
    FORCE_ON = 1
    FORCE_OFF = 0
    BY_IMAGE = 2

def ceil_y_limit(y) :
    """ Ceil Y limit to nearest power of 10. """
    d = len(str(int(y)))
    p = 10 ** (d-1)
    return (int(y / p) + 1) * p

# Make visual log folder to home folder.
def make_vlog_dir(sub_dir="vlog") :
    """ Make visual log directory in home folder. """
    homedir = os.environ['HOME']
    vlog_dir = os.path.join(homedir, sub_dir)
    os.makedirs(vlog_dir, exist_ok = True)
    return vlog_dir

# Get resize factor from long side of image.
def get_resize_factor(longer_side) :
    """ Get resize factor from long side of image. """
    f = 1
    if BIG_LONGSIDE < longer_side :
        f = 1/4
    elif SMALL_LONGSIDE < longer_side <= BIG_LONGSIDE :
        f = 1/2
    return f

# Detecting images edges using Sobel filter.
def get_sobel_edges(image, ddepth, kernel) :
    """ Make edge image using Sobel filter """
    sobel_x = cv.convertScaleAbs(cv.Sobel(image, ddepth, 1, 0, kernel))
    sobel_y = cv.convertScaleAbs(cv.Sobel(image, ddepth, 0, 1, kernel))
    edges = cv.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0)
    return edges

# Detecting image edges using Canny filter.
def get_canny_edges(image, sigma) :
    """ Make edge image using Canny filter """
    median_value = np.median(image)
    min_value = int( max(0, (1.0-sigma) * median_value) )
    max_value = int( max(255, (1.0+sigma) * median_value) )
    edges = cv.Canny(image, min_value, max_value)
    return edges

# Metering image power using foulier transform.
def get_foulier_power(image) :
    """ Metering image power using foulier transform. """
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
ap.add_argument("--face-detect", help = "face detect", action = argparse.BooleanOptionalAction,
                 default = True)
ap.add_argument("-so", "--sobel", help = "force sobel", action = 'store_true', default = False)
ap.add_argument("-m", "--model", help = "model", default = "yunet.onnx")
ap.add_argument("-nm", "--normalize", help = "normalize image",
                 action = argparse.BooleanOptionalAction, default = argparse.SUPPRESS)
ap.add_argument("-vl", "--vlog", help = "save visual log", action = 'store_true', default = False)

args = vars(ap.parse_args())

# Parseing additional parameters.
verbose = args["v"]
filter_kernel = args["k"]
filter_ddepth = cv.CV_32F if (args["d"] == 32) else cv.CV_8U
if "normalize" in args :
    if args["normalize"] is True :
        NORMALIZATION = NORMALIZE.FORCE_ON
    else :
        NORMALIZATION = NORMALIZE.FORCE_OFF
else :
    NORMALIZATION = NORMALIZE.BY_IMAGE

start_point = time.perf_counter()

script_path = os.path.dirname(os.path.abspath(__file__))
fd_model = os.path.join(script_path, args["model"])
if verbose >= 5 :
    print("model=", fd_model)

# Exists check for Model file.
if os.path.isfile(fd_model) is not True :
    sys.exit(ERROR_CANTOPEN)

image_path = args["file"]
if verbose >= 1 :
    print("input image=", image_path)
# Input image exist check.
if os.path.isfile(image_path) is not True :
    print(image_path, " NOT EXISTS.")
    sys.exit(ERROR_CANTOPEN)
# Read image.
original_image = cv.imread(image_path)
if original_image is None :
    print(image_path, " CAN'T READ.")
    sys.exit(ERROR_CANTOPEN)

if verbose >= 2 :
    print("original size=",original_image.shape)

# Image resizing fot face detect.
orig_height, orig_width, _ = original_image.shape
long_side = max(orig_height, orig_width)
factor = get_resize_factor(long_side)
if verbose >= 2 :
    print("resize factor=", factor)

if factor != 1.0 :
    resized_image = cv.resize(original_image, None, fx=factor, fy=factor,
                    interpolation=cv.INTER_NEAREST_EXACT)
else :
    resized_image = original_image.copy()

after_resize = time.perf_counter()

if verbose >= 2 :
    print("resized image=", resized_image.shape)

# Detecting faces.
resized_height, resized_width, _ = resized_image.shape
resized_pixels = resized_height * resized_width
if args["face_detect"] :
    fd = cv.FaceDetectorYN_create(fd_model, "", (resized_width, resized_height))
    fd.setScoreThreshold(SCORE_THRESHOLD)
    fd.setTopK(TOP_K)
    _, faces = fd.detect(resized_image)
else :
    faces = None

after_fd = time.perf_counter()

face_count = len(faces) if faces is not None else 0
if verbose >= 1 :
    print("faces=", face_count)

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

# Iterate loop with detected faces.
for img_it in faces :

    if verbose >= 1 :
        print("area", count, end=": ")

    face_width = int(img_it[FACE.WIDTH])
    face_height = int(img_it[FACE.HEIGHT])
    if verbose >= 2 :
        print(f"width={face_width}, height={face_height}", end = ", ")

    # If face size is too small, skip it.
    face_pixels = face_width * face_height
    if face_pixels / resized_pixels < IGNORE_FACE_FACTOR :
        if verbose >= 1 :
            print("It's too small face, skipped.")
        count += 1
        continue

    # Get mouth detecting result
    face_rmouth_x = int(img_it[FACE.RMOUTH_X])
    face_lmouth_x = int(img_it[FACE.LMOUTH_X])
    if (face_count >= 1 and verbose >= 3) :
        print(f"mouth=({face_rmouth_x},{face_lmouth_x})", end = ", ")

    # Get eye detecting result
    face_leye_x = int(img_it[FACE.LEYE_X])
    face_reye_x = int(img_it[FACE.REYE_X])
    if (face_count >= 1 and verbose >= 3) :
        print(f"eye=({face_reye_x},{face_leye_x})", end = ", ")

    # Get nose detecting result
    face_nose_x = int(img_it[FACE.NOSE_X])
    face_nose_y = int(img_it[FACE.NOSE_Y])
    if (face_count >= 1 and verbose >= 3) :
        print(f"nose=({face_nose_x},{face_nose_y})", end = ", ")

    # Get face detecting result
    face_score = round(img_it[FACE.SCORE], 2) if face_count >= 1 else 0.0
    # Crop face
    img_x1 = 0 if (img_it[FACE.X] < 0) else int(img_it[FACE.X])
    img_x2 = img_x1 + int(img_it[FACE.WIDTH])
    img_y1 = 0 if (img_it[FACE.Y] < 0) else int(img_it[FACE.Y])
    img_y2 = img_y1 + int(img_it[FACE.HEIGHT])
    crop_image = resized_image[img_y1 : img_y2, img_x1 : img_x2]
    if verbose >= 5 :
        print (f"image x1={img_x1},x2={img_x2},y1={img_y1},y2={img_y2}")

    std_dev = round(np.std(crop_image), 2)
    if verbose >= 2 :
        print(f"stddev={std_dev}", end=", ")

    if (NORMALIZATION == NORMALIZE.FORCE_ON or
        NORMALIZATION == NORMALIZE.BY_IMAGE and face_count == 0 or std_dev < NORMALIZE_THRESHOLD) :
        # Normalize image if option is set or face not found.
        if verbose >= 2 :
            print("normalize=on", end=", ")
        crop_image = cv.normalize(crop_image, None, 0, 255, cv.NORM_MINMAX)
    else :
        if verbose >= 2 :
            print("normalize=off", end=", ")

    # Grayscale conversion.
    gray_image = cv.cvtColor(crop_image, cv.COLOR_BGR2GRAY)

    # Make edge image
    if args["sobel"] is True :
        # Sobel filter
        edge_image = get_sobel_edges(gray_image, filter_ddepth, filter_kernel)
    else :
        # Laplacian conversion
        edge_image = cv.Laplacian(gray_image, filter_ddepth, filter_kernel)

    # Get histogram from edge image.
    (hist, bins) = np.histogram(edge_image, bins = HIST_BINS, range = (0,256))
    power_length = len(hist)

    # Determine start/end for power calculation.
    power_start = 0
    power_end = 0
    # Seeking power_start and power_end.
    for i in range((power_length - 1), ((power_length // 3) * 2), -1) :
        # Find first point of hist[] not zero
        if power_end == 0 and hist[i] != 0 :
            power_end = i
            break
    # if power_end is not found, edge image has no edge, skip power calculation.
    if power_end == 0 :
        power_start = power_length - 1
        power_end = power_length - 1
    else :
        power_start = power_end - (POWER_RANGE - 1)
        power_start = max(power_start, 0)

    if verbose >= 3 :
        print("power_start=", power_start, end=", ")
        print("power_end=", power_end, end=", ")
        if verbose >= 4 :
            print()
            print("hist=", hist)
        else :
            print("hist=", hist[ power_start : power_end + 1], end=", ")

    # Calculate power of current face.
    power = 0
    for i in range(power_start, power_end + 1) :
        power += hist[i] * i
    # Power deducted by dispartion of histgrom
    if power_end == MAX_BIN_INDEX :
        power *= 1.25
    else :
        if power_end == (MAX_BIN_INDEX - 1) :
            power *= 1.1
        if POWER_END_GATE < power_end < POWER_END_DESCEND :
            power *= 0.75
    # Power deducted by face detection result
    if face_count != 0 :
        if face_rmouth_x <= 0 and face_lmouth_x <= 0 :
            power *= MOUTH_DEDUCT
        if face_reye_x <= 0 and face_leye_x <= 0 :
            power *= EYE_DEDUCT
        if face_nose_x <= 0 and face_nose_y <= 0 :
            power *= NOSE_DEDUCT

    if verbose >= 1 :
        print("power=", power, end=", ")

    if verbose >= 1 and face_count >= 1 :
        print("score=", face_score, end=", ")

    # Flashing max_power
    if power > max_power and power_end > POWER_END_GATE :
        max_power = power
        max_index = count
    if verbose >= 1 :
        print()

    count += 1
# End iteration of faces.

# Evaluate face has max_power.
if max_power < 0 :
    #It seems no face through POWER_GATE in image or too small face.
    result = 0
    face_count = 0
else :
    max_face = faces[max_index]
    max_width = int(max_face[FACE.WIDTH])
    max_height = int(max_face[FACE.HEIGHT])
    max_score = max_face[FACE.SCORE]

    # Make slope for image(face) has low score.
    max_power *= ((max_score + POWER_SLOPE) ** 2) if (max_score < POWER_CLIFF) else max_score

    if verbose >= 3 :
        print(f"max width={max_width}, height={max_height}")
    # if face count is 0, use half of image size as ROI.
    if face_count == 0 :
        max_width /= 2
        max_height /= 2

    pixel_count = int(max_width * max_height / PIXEL10K)

    # Rounds up for too small face.
    pixel_count = max(pixel_count, 1)
    # Make result.
    power_kpixel = max_power / pixel_count
    result = round(power_kpixel)
    if verbose >= 2 :
        print("10Kpixels=", pixel_count)
        print("max power=", max_power)
        print("power/10Kpixels=", power_kpixel)

# Output result to stdout.
if verbose >= 1 :
    print("result=", result)
else :
    print(f"value={result},face_count={face_count}")

end_point = time.perf_counter()
if verbose >= 4 :
    print(f"until resize time : {after_resize - start_point:.3f} sec.")
    print(f"until fd time: {after_fd - start_point:.3f} sec.")
    print(f"total time: {end_point - start_point:.3f} sec.")

# Make 'visual log' by option.
if args["vlog"] :
    # Create visual log folder.
    report_dir = make_vlog_dir()
    base_name = os.path.basename(image_path)
    (base_noext, ext) = os.path.splitext(base_name)
    # Draw result for face has max power
    vlog_line = max(resized_width, resized_height) // 1000
    vlog_line = max(vlog_line, 3)

    if face_count >= 1 :

        box = list(map(int, max_face[:4]))
        max_x = int(max_face[FACE.X])
        max_y = int(max_face[FACE.Y])
        max_rmouth_x = int(max_face[FACE.RMOUTH_X])
        max_rmouth_y = int(max_face[FACE.RMOUTH_Y])
        max_lmouth_x = int(max_face[FACE.LMOUTH_X])
        max_lmouth_y = int(max_face[FACE.LMOUTH_Y])

        cv.rectangle(resized_image, box, COLOR.BLUE, vlog_line)
        cv.putText(resized_image, str(face_score), (max_x, (max_y - 8)),
                    cv.FONT_HERSHEY_DUPLEX, 0.8, COLOR.CYAN, 2)
        cv.circle(resized_image, [max_rmouth_x, max_rmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
        cv.circle(resized_image, [max_lmouth_x, max_lmouth_y], 5, COLOR.MAGENTA, -1, cv.LINE_AA)
        cv.circle(resized_image, [int(max_face[FACE.REYE_X]), int(max_face[FACE.REYE_Y])],
                   5, COLOR.RED, -1, cv.LINE_AA)
        cv.circle(resized_image, [int(max_face[FACE.LEYE_X]), int(max_face[FACE.LEYE_Y])],
                   5, COLOR.RED, -1, cv.LINE_AA)
        cv.circle(resized_image, [int(max_face[FACE.NOSE_X]), int(max_face[FACE.NOSE_Y])],
                   5, COLOR.GREEN, -1, cv.LINE_AA)
    # End if (face_count >= 1)
    # Draw total result
    cv.putText(resized_image, ("Result=" + str(result)), (32, 64),
                    cv.FONT_HERSHEY_SIMPLEX, 2.0, COLOR.RED, 6)
    cv.putText(resized_image, ("StdDev=" + str(std_dev)), (32, 100),
                    cv.FONT_HERSHEY_SIMPLEX, 1.0, COLOR.MID_YELLOW, 2)

    # Overlay edge image on left bottom of image.
    edge_image = cv.cvtColor(edge_image, cv.COLOR_GRAY2BGR)
    (edge_height, edge_width) = edge_image.shape[:2]
    if face_count == 0 :
        # If no face detected(size of edge image = resized image), crop edge image to 1/3 of image.
        crop_height = edge_height // 3
        crop_width = edge_width // 3
        (x1, y1) = (crop_width, crop_height)
        (x2, y2) = (x1 + crop_width, y1 + crop_height)
        edge_image = edge_image[y1 : y2, x1 : x2]
        (edge_height, edge_width) = edge_image.shape[:2]
    (roi_x1, roi_y1) = (IMPOSE_OFFSET, resized_height - IMPOSE_OFFSET - edge_height)
    (roi_x2, roi_y2) = (roi_x1 + edge_width, roi_y1 + edge_height)
    cv.rectangle(resized_image, (roi_x1, roi_y1),(roi_x2, roi_y2),
                  (COLOR.GREEN if (face_count == 0) else COLOR.BLUE), vlog_line)
    resized_image[roi_y1 : roi_y2, roi_x1 : roi_x2] = edge_image

    # Overlay histogram image
    import matplotlib.pyplot as plt
    import io
    from PIL import Image

    plt.stairs(hist, bins, fill = True)
    plt.title(base_name)
    plt.xlabel("Edge Intensity")
    plt.ylabel("Count")
    plt.grid()
    plt.ylim(0, ceil_y_limit(hist[ (HIST_BINS // 4) ]))
    buffer = io.BytesIO()
    plt.savefig(buffer, dpi = PLOT_DPI)
    plt.close()
    buffer.seek(0)
    plot_image = Image.open(buffer)
    plot_image = np.array(plot_image)
    plot_image = cv.cvtColor(plot_image, cv.COLOR_RGBA2BGR)
    # overlay histogram image on right bottom of image.
    (plot_height, plot_width) = plot_image.shape[:2]
    roi_y2 = resized_height - IMPOSE_OFFSET
    roi_y1 = roi_y2 - plot_height
    roi_x2 = resized_width - IMPOSE_OFFSET
    roi_x1 = roi_x2 - plot_width
    resized_image[roi_y1 : roi_y2, roi_x1 : roi_x2] = plot_image
    # write vlog image
    vlog_file_path = os.path.join(report_dir, base_noext + "_vlog" + ext)
    cv.imwrite(vlog_file_path, resized_image)
    if verbose >= 1 :
        print("visual log=", vlog_file_path)
    # End of visual log.

# Return value to OS
if result > MAX_RESULT :
    result = MAX_RESULT
elif 0 <= result < MIN_RESULT :
    result = MIN_RESULT
sys.exit(result)
