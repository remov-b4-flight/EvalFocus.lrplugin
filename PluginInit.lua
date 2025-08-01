--[[-------------------------------------------------------
EvalFocus.lrdevplugin
@file	PluginInit.lua
@brief	Initialize routines when EvalFocus.lrdevplugin Plugin is loaded. 
@author	remove-b4-flight
---------------------------------------------------------]]
local prefs = import 'LrPrefs'.prefsForPlugin() 

if prefs.AutoReject == nil then
	prefs.AutoReject = false
end
if prefs.RejectRange == nil then
	prefs.RejectRange = 30
end
if prefs.Vlog == nil then
	prefs.Vlog = false
end
if prefs.Title == nil then
	prefs.Title = "EvalFocus"
end