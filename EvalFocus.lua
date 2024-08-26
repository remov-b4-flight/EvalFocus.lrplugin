--[[
EvalFocus.lrdevplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

--[[ Please specify python at your environment.]]
local python = '/opt/homebrew/bin/python3'

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
--local LrLogger = import 'LrLogger'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local LrSelection = import 'LrSelection'
--local Logger = LrLogger(PluginTitle)
local prefs = import 'LrPrefs'.prefsForPlugin()

--Logger:enable('logfile')

local MINRESULT = 5
--local LOW_BRISQUE = 4
local CurrentCatalog = LrApplication.activeCatalog()
local script = '/evalfocus.py '
local script_path = _PLUGIN.path .. ' ' ..script

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
		for i,PhotoIt in ipairs(SelectedPhotos) do
			if (PhotoIt:getRawMetadata('fileFormat') == 'JPG') then 
				local FilePath = PhotoIt:getRawMetadata('path')
				local CommandLine = python .. script_path .. FilePath  
--				Logger:info(FilePath)
				local r = LrTasks.execute(CommandLine)
				local value = r / 256
--				Logger:info('value=' .. value)
				if (MINRESULT <= value) then
					PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', value)
					if (prefs.AutoReject == true  and value < prefs.RejectRange) then
--						if (value == LOW_BRISQUE) then
--							Logger:warn('rejected by low BRISQUE.')
--						else
--							Logger:warn('rejected by value.')
--						end
						PhotoIt:setRawMetadata('pickStatus', -1)
					end
				else
--					Logger:error('retern indicates some error.')
				end
			else
--				Logger:info('skip non JPEG file.')
			end --isVideo
			ProgressBar:setPortionComplete(i, countPhotos)
		end --end of for photos loop
		ProgressBar:done()
	end, { timeout = 0.1 } ) --end of withWriteAccessDo
	LrSelection.selectNone()
end ) --end of startAsyncTask function()
return
