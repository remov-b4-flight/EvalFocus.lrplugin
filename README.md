# EvalFocus.lrplugin
EvalFocus-plugin
Evalfocus is Adobe Lightroom plugin that evaluate correct focus on photo.
## pre-requesties
* Windows10
* WSL
* ubuntu(on WSL)
* on WSL ubuntu, install python3/opencv/opencv-data
## install
* install Evalfocus.lrplugin as normal lightroom plugin
* make symbolic link on plugin path to /usr/share/opencv4/haarcacades/haarcacade_frontalface.xml
* same also /usr/share/opencv4/haarcacades/haarcacade_profileface.xml
* same also /usr/share/opencv4/haarcacades/haarcacade_eye.xml
## use
Select Photos and Select Lightroom menu Library->Plugin Extra->Evalfocus->evaluate
results are appeared as custom metadata 'accuracy' as number.
About 100 or more can be judged as focus is collect.
## Licence
GPLv3
