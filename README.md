# EvalFocus.lrplugin
EvalFocus-plugin
Evalfocus is Adobe Lightroom plugin that evaluate correct focus on photo.
## pre-requesties
* MacOS
* Lightroom
* homebrew
* OpenCV
* pip opcncv-python / opencv-pyton-contrib
## install
* install Evalfocus.lrplugin as normal lightroom plugin
* make symbolic link on plugin path to /usr/share/opencv4/haarcacades/haarcacade_frontalface.xml
* same also /usr/share/opencv4/haarcacades/haarcacade_profileface.xml
* same also /usr/share/opencv4/haarcacades/haarcacade_eye.xml
## use
Select Photos and Select Lightroom menu Library->Plugin Extra->Evalfocus->evaluate
results are appeared as custom metadata 'Value' as string-nized number.
And 'Rank' as indicate photo is able to delete.
## Licence
GPLv3
