--[[
EvalFocus.lrdevplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

-- Please specfy python in your local enviromnent.
local python = '/opt/homebrew/bin/python3.12'

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local LrSelection = import 'LrSelection'
local LrFileUtils = import 'LrFileUtils'
local prefs = import 'LrPrefs'.prefsForPlugin()

--local LrLogger = import 'LrLogger'
--local Logger = LrLogger(PluginTitle)
--Logger:enable('logfile')

--Constants
local SEP = ' '
local OUTOP = '-o'
local script = '/evalfocus.py'
local script_path = _PLUGIN.path .. script
local MINRESULT = 5
local NOTFOUND = 2

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
		{title = PluginTitle .. ' Running..'}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	local c = math.log(countPhotos, 10)
	local pgtick = 10
	if ( c > 3.0 ) then
		pgtick = 100
	elseif (c > 2.6) then
		pgtick = 25
	end
	--loops photos in selected
	CurrentCatalog:withWriteAccessDo('Evaluate Focus', function()
		for i,PhotoIt in ipairs(SelectedPhotos) do
			if (PhotoIt:getRawMetadata('fileFormat') == 'JPG') then 
				local FilePath = PhotoIt:getRawMetadata('path')
				local TempPath = os.tmpname()
				local CommandLine = python .. SEP .. script_path .. SEP .. FilePath .. SEP .. OUTOP .. SEP .. TempPath
--				Logger:info(CommandLine)
				-- only MSB 8 bits are valid
				local retval = LrTasks.execute(CommandLine) / 256
				-- get results to file
				local contents = LrFileUtils.readFile(TempPath)
				local value = FOTFOUND
				if (string.len(contents) > 0) then
					value = tonumber(contents)
				end
				LrFileUtils.delete(TempPath)
--				Logger:info('value=' .. value)
				if (value >= MINRESULT) then 
					PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', value)
					if (prefs.AutoReject == true and value < prefs.RejectRange) then
						PhotoIt:setRawMetadata('pickStatus', -1)
					end
				end
			else
--				Logger:info('skip non JPEG file.')
			end --isVideo
			if ((i % pgtick) == 0) then 
				ProgressBar:setPortionComplete(i, countPhotos)
			end
		end --end of for photos loop
		ProgressBar:done()
	end, { timeout = 0.1 } ) --end of withWriteAccessDo
	LrSelection.selectNone()
end ) --end of startAsyncTask function()
return
