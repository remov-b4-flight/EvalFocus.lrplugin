--[[
EvalFocus.lrdevplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

-- Please specfy python in your local enviromnent.
local python = '/opt/homebrew/bin/python3'

local LrApplication = import 'LrApplication'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local LrSelection = import 'LrSelection'
local LrFileUtils = import 'LrFileUtils'
local prefs = import 'LrPrefs'.prefsForPlugin()

--local LrLogger = import 'LrLogger'
--local Logger = LrLogger(prefs.Title)
--Logger:enable('logfile')

--Constants
local SEP = ' '
local SCRIPT = '/evalfocus.py'
local SCRIPT_PATH = _PLUGIN.path .. SCRIPT
local OPTION = "-g"
local MINRESULT = 5
local NOTFOUND = 2
--For python logfile
local REDIR = '>>'
local LOG_OPTION = '-vvvv'
local LOG_FILE = '/evalfocus.log'
local LOGPATH = _PLUGIN.path .. LOG_FILE
local LOG_CMDLINE = LOG_OPTION .. SEP .. REDIR .. SEP .. LOGPATH

if (prefs.AutoReject == nil) then
	prefs.AutoReject = false
end
if (prefs.RejectRange == nil) then
	prefs.RejectRange = 30
end

local CurrentCatalog = LrApplication.activeCatalog()

--Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = prefs.Title .. ' is running..'}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	--loops photos in selected
	for i,PhotoIt in ipairs(SelectedPhotos) do
		if (ProgressBar:isCanceled()) then
			ProgressBar:done()
			return
		end
		if (PhotoIt:getRawMetadata('fileFormat') == 'JPG' and PhotoIt:getRawMetadata('fileSize') ~= nil ) then 
			local FilePath = PhotoIt:getRawMetadata('path')
			local CommandLine = python .. SEP .. SCRIPT_PATH .. SEP .. OPTION .. SEP .. FilePath
--			Logger:info(CommandLine)
			-- only MSB 8 bits are valid
			local return_value = LrTasks.execute(CommandLine) / 256
--			Logger:info('value=' .. return_value)
			if (return_value >= MINRESULT) then 
				CurrentCatalog:withWriteAccessDo('Evaluate Focus', function()
					PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', return_value)
					if (prefs.AutoReject == true and return_value < prefs.RejectRange) then
						PhotoIt:setRawMetadata('pickStatus', -1)
						PhotoIt:setRawMetadata('colorNameForLabel','blue')
					end
				end, { timeout = 0.33 } ) --end of withWriteAccessDo 					
			end
		else
--			Logger:info('skip non JPEG file.')
		end --isVideo
		ProgressBar:setPortionComplete(i, countPhotos)
	end --end of for photos loop
	ProgressBar:done()
	LrSelection.selectNone()
end ) --end of startAsyncTask function()
return
