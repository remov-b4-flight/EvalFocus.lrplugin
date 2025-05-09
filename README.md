# EvalFocus.lrplugin
EvalFocus is Adobe Lightroom Classic plugin that evaluate correct focus on JPEG photo.
Mainly developed for macOS environment. I have no Windows environment.
## pre-requesties
* macOS
* Lightroom Classic
* homebrew
* OpenCV
* numpy
* matplotlib (optional)
* pip modules opcncv-python / opencv-pyton-contrib
## install
* Install EvalFocus.lrplugin as normal lightroom plugin
* Download and copy as 'yunet.onnx from [GitHub](https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx)
## use
Select Photos and Select Lightroom menu Library->Plugin Extra->Evalfocus->evaluate
results are appeared as custom metadata 'Value' as string-nized number.
And Added reject flag that 'Value' below from plugin setting 'Autoreject' value
## Disclaimer
The developers shall not be held liable for any damages arising from the use of this software. Use it at your own risk.
If you use this of software, The final decision of deletion is yours.
## Licence
GPLv3
