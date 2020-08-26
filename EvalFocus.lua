--[[
EvalFocus.lua
EvalFocus.lrplugin
Author:@remov_b4_flight
]]

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrLogger = import 'LrLogger'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local Logger = LrLogger (PluginTitle)

Logger:enable('logfile')
local info = Logger:quickf('info')

local CurrentCatalog = LrApplication.activeCatalog()
local shell = 'c:\\windows\\system32\\wsl.exe -e '
local python = 'python3 '
local script = '/evalfocus.py -v '
local wsl_pfx = '/mnt/'
local redir_file = ' >>'.. _PLUGIN.path .. '/evalfocus.log' 

function get_wslpath(winpath)
	local wkpath = (winpath:gsub('\\','/')):sub(3)
	local drive = (winpath:sub(1,1)):lower()
	local p = wsl_pfx .. drive .. wkpath
	return p
end

--Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = PluginTitle .. ' Processing'}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	--loops photos in selected
	info('-loop-')
	CurrentCatalog:withWriteAccessDo('Evaluate Focus',function()
		local script_path = get_wslpath(_PLUGIN.path) .. script
		for i,PhotoIt in ipairs(SelectedPhotos) do
			local winpath = PhotoIt:getRawMetadata('path')
			local FilePath = get_wslpath(winpath)
			local CommandLine = shell .. python .. script_path .. FilePath  .. redir_file
			info(CommandLine)
			local Accuracy = LrTasks.execute(CommandLine)
			info ('Accuracy=' .. Accuracy)
			PhotoIt:setPropertyForPlugin(_PLUGIN,'accuracy',Accuracy)
			ProgressBar:setPortionComplete(i,countPhotos)
		end --end of for photos loop
	end ) --end of withWriteAccessDo
ProgressBar:done()
info('-end-')
end ) --end of startAsyncTask function()
return
