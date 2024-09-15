# EvalFocus.lrplugin
EvalFocus-plugin
Evalfocus is Adobe Lightroom Classic plugin that evaluate correct focus on JPEG photo.
Mainly developed for Mac environment. I have no Windows environment.
## pre-requesties
* MacOS
* Lightroom
* homebrew
* OpenCV
* numpy
* pip modules opcncv-python / opencv-pyton-contrib
## install
* install Evalfocus.lrplugin as normal lightroom plugin
* make symbolic link each yml files on plugin path /opt/homebrew/Celllar/opencv/[version]/share/opencv4/quality to plugin folder
## use
Select Photos and Select Lightroom menu Library->Plugin Extra->Evalfocus->evaluate
results are appeared as custom metadata 'Value' as string-nized number.
And Added reject flag that 'Value' below from plugin setting 'Autoreject' value
## Licence
GPLv3
