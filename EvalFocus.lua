--[[
EvalFocus.lrplugin
@file EvalFocus.lua
@author @remov_b4_flight
]]

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrLogger = import 'LrLogger'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local Logger = LrLogger (PluginTitle)

Logger:enable('logfile')
local info = Logger:quickf('info')

local AutoReject = 30
local MINRESULT = 5

local CurrentCatalog = LrApplication.activeCatalog()
local shell = 'c:\\windows\\system32\\wsl.exe -e '
local python = 'python3 '
local script = '/evalfocus.py '
local wsl_pfx = '/mnt/'
--local redir_file = ' >>'.. _PLUGIN.path .. '\\evalfocus.log' 

function get_wslpath(winpath)
	local wkpath = (winpath:gsub('\\','/')):sub(3)
	local drive = (winpath:sub(1,1)):lower()
	local p = wsl_pfx .. drive .. wkpath
	return p
end

function getRank(accuracy)
	local r = nil
	if (accuracy >= 200) then r = 'A++'
	elseif (accuracy >= 150) then r = 'A+'
	elseif (accuracy >= 100) then r = 'A'
	elseif (accuracy >= 50) then r = 'B'
	elseif (accuracy >= MINRESULT) then r = 'C'
	end
	return r
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
	CurrentCatalog:withWriteAccessDo('Evaluate Focus',function()
		local script_path = get_wslpath(_PLUGIN.path) .. script
		info('-loop-')
		for i,PhotoIt in ipairs(SelectedPhotos) do
			local winpath = PhotoIt:getRawMetadata('path')
			local FilePath = get_wslpath(winpath)
			local CommandLine = shell .. python .. script_path .. FilePath 
			info(FilePath)
			local Accuracy = LrTasks.execute(CommandLine)
			info ('Accuracy = ' .. Accuracy)
			if (MINRESULT <= Accuracy) then

				PhotoIt:setPropertyForPlugin(_PLUGIN,'accuracy',Accuracy)
				local Rank = getRank(Accuracy)
				if Rank ~= nil then
					info ('Rank = ' .. Rank)
					PhotoIt:setPropertyForPlugin(_PLUGIN,'rank',Rank)
				end
				if (Accuracy < AutoReject) then
					PhotoIt:setRawMetadata('pickStatus', -1)
				end
			end
			ProgressBar:setPortionComplete(i,countPhotos)
		end --end of for photos loop
		ProgressBar:done()
	end ) --end of withWriteAccessDo
info('-end-')
end ) --end of startAsyncTask function()
return
