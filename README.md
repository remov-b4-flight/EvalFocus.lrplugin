# EvalFocus.lrdevplugin
EvalFocus-plugin
Evalfocus is Adobe Lightroom plugin that evaluate correct focus on photo.
## pre-requesties
* MacOS
* Lightroom
* homebrew
* OpenCV
* pip modules opcncv-python / opencv-pyton-contrib
## install
* install Evalfocus.lrplugin as normal lightroom plugin
* make symbolic link on plugin path /opt/homebrew/Celllar/opencv/[version]/share/opencv4/quality to /opt/homebrew/share/opencv4/quality
## use
Select Photos and Select Lightroom menu Library->Plugin Extra->Evalfocus->evaluate
results are appeared as custom metadata 'Value' as string-nized number.
And 'Rank' as indicate photo is able to delete.
## Licence
GPLv3
