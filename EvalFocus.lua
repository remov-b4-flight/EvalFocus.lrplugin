--[[
EvalFocus.lua
EvalFocus.lrplugin
Author:@jenoki48
]]

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrLogger = import 'LrLogger'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
--local LrDate = import 'LrDate'
local EVLogger = LrLogger (PluginTitle)
--local LrShell = import 'LrShell'
--local LrDialogs = import 'LrDialogs'
--local LrFileUtils = import 'LrFileUtils'

EVLogger:enable('logfile')
local info = EVLogger:quickf('info')

local CurrentCatalog = LrApplication.activeCatalog()
local evalfocus = '/opt/local/bin/evalfocus'
local logfile = '/Users/jenoki/Documents/evalcmd.log'
local log_option = ' -l  ' .. logfile .. ' '

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
		for i,PhotoIt in ipairs(SelectedPhotos) do
			info("Identifier=%d",PhotoIt.localIdentifier)

			local FilePath = PhotoIt:getRawMetadata('path')
			local Argument = log_option
			local CommandLine = evalfocus .. Argument .. "-f '" .. FilePath .."' "
			info(CommandLine)
			local Accuracy = LrTasks.execute(CommandLine) / 256
			info ('Accuracy=' .. Accuracy)
			PhotoIt:setPropertyForPlugin(_PLUGIN,'accuracy',Accuracy)
			ProgressBar:setPortionComplete(i,countPhotos)
		end --end of for photos loop
	end ) --end of withWriteAccessDo
ProgressBar:done()
info('-end-')
end ) --end of startAsyncTask function()
return
