--[[
EvalFocus.lrdevplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrLogger = import 'LrLogger'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local Logger = LrLogger(PluginTitle)
local prefs = import 'LrPrefs'.prefsForPlugin()

Logger:enable('logfile')

local MINRESULT = 5
local CurrentCatalog = LrApplication.activeCatalog()
local python = '/opt/homebrew/bin/python3 '
local script = '/evalfocus.py '
local script_path = _PLUGIN.path .. script

if (prefs.AutoReject == nil) then
	prefs.AutoReject = false
end
if (prefs.RejectRange == nil) then
	prefs.RejectRange = 30
end

--Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = PluginTitle .. ' Running..'}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	--loops photos in selected
	CurrentCatalog:withWriteAccessDo('Evaluate Focus', function()
		Logger:debug('-loop-')
		for i,PhotoIt in ipairs(SelectedPhotos) do
			local FilePath = PhotoIt:getRawMetadata('path')
			local CommandLine = python .. script_path .. FilePath  
			Logger:debug(FilePath)
			local value = LrTasks.execute(CommandLine) / 256
			Logger:debug('value = ' .. value)
			if (MINRESULT <= value) then

				PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', value)
				if (prefs.AutoReject == true  and value < prefs.RejectRange) then
					Logger:debug('rejected by value.')
					PhotoIt:setRawMetadata('pickStatus', -1)
				end
			end
			ProgressBar:setPortionComplete(i, countPhotos)
		end --end of for photos loop
		ProgressBar:done()
	end ) --end of withWriteAccessDo
Logger:debug('-end-')
end ) --end of startAsyncTask function()
return
