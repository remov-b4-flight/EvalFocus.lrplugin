--[[
EvalFocus.lrdevplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

-- split string from evalfocus.py
function KeyValueSplit(s, delim)
	local result = {}
	for match in (s..delim):gmatch("(.-)"..delim) do
		local key, value = match:match("([^=]+)=([^=]+)")
		if key and value then
			result[key] = value
		end
	end
	return result
end
-- Please specfy python in your local enviromnent.
local python = '/opt/homebrew/bin/python3'

local LrApplication = import 'LrApplication'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local LrSelection = import 'LrSelection'
--local LrFileUtils = import 'LrFileUtils'
local prefs = import 'LrPrefs'.prefsForPlugin()

if (prefs.AutoReject == nil) then
	prefs.AutoReject = false
end
if (prefs.RejectRange == nil) then
	prefs.RejectRange = 30
end
if (prefs.Vlog == nil) then
	prefs.Vlog = false
end

--local LrLogger = import 'LrLogger'
--local Logger = LrLogger(prefs.Title)
--Logger:enable('logfile')

--Constants
local SEP = ' '
local SCRIPT = '/evalfocus.py'
local SCRIPT_PATH = _PLUGIN.path .. SCRIPT
local OPTION = " "
local MINRESULT = 5
--local NOTFOUND = 2
-- For python logfile
--local REDIR = '>>'
--local LOG_OPTION = '-vvvv'
--local LOG_FILE = '/' .. prefs.Title .. '.log'
--local LOGPATH = _PLUGIN.path .. LOG_FILE
--local LOG_CMDLINE = LOG_OPTION .. SEP .. REDIR .. SEP .. LOGPATH

local CurrentCatalog = LrApplication.activeCatalog()

if prefs.Vlog == true then
	OPTION = " -vl" .. OPTION
end

--Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = prefs.Title .. ' is running..'}
	)
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	if (countPhotos > 1) then
		LrSelection.selectNone()
	end
	--loops photos in selected
	for i,PhotoIt in ipairs(SelectedPhotos) do
		-- check if the user has canceled the operation
		if (ProgressBar:isCanceled()) then
			break
		end
		if (PhotoIt:getRawMetadata('fileFormat') == 'JPG' and PhotoIt:getRawMetadata('fileSize') ~= nil ) then 
			local FilePath = PhotoIt:getRawMetadata('path')
			local CommandLine = python .. SEP .. SCRIPT_PATH .. SEP .. OPTION .. SEP .. FilePath
--			Logger:info(CommandLine)
			local stdin = io.popen(CommandLine, 'r')
			if(stdin == nil) then
				ProgressBar:done()
				return
			end
			local eval_string = stdin:read('*a')
			stdin:close()
			local eval_table = KeyValueSplit(eval_string, ',')
			local result_value = tonumber(eval_table['value']) or 0
			local face_count = tonumber(eval_table['face_count']) or 0
--			Logger:info('value=' .. result_value)
--			Logger:info('face_count=' .. face_count)
			if (result_value >= MINRESULT) then 
				CurrentCatalog:withPrivateWriteAccessDo( function()
					PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', result_value)
					PhotoIt:setPropertyForPlugin(_PLUGIN, 'face_count', face_count)
					if (prefs.AutoReject == true and result_value < prefs.RejectRange) then
						CurrentCatalog:withWriteAccessDo( prefs.Title, function()
							PhotoIt:setRawMetadata('pickStatus', -1)
							PhotoIt:setRawMetadata('colorNameForLabel','blue')
						end, { timeout = 0.33 } ) --end of withWriteAccessDo
					end
				end, { timeout = 0.33 } ) --end of withWriteAccessDo 					
			end
		else
--			Logger:info('skip non JPEG file.')
		end --isVideo
		ProgressBar:setPortionComplete(i, countPhotos)
	end --end of for photos loop
	ProgressBar:done()
	if (#CurrentCatalog:getTargetPhotos() > 1) then
		LrSelection.selectNone()
	end
end ) --end of startAsyncTask function()
return
