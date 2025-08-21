--[[
EvalFocus.lrplugin
@file EvalClear.lua
@author @remov_b4_flight
@brief Clear evaluation results for selected photos
]]

local prefs = import 'LrPrefs'.prefsForPlugin()
local LrApplication = import 'LrApplication'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'
local TIMEOUT = 0.5

local CurrentCatalog = LrApplication.activeCatalog()

-- Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = ' Clearing ' .. prefs.Title .. ' results..',}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	-- loops photos in selected
	CurrentCatalog:withPrivateWriteAccessDo( function()
		for i,PhotoIt in ipairs(SelectedPhotos) do
				PhotoIt:setPropertyForPlugin(_PLUGIN, 'value', nil)
				PhotoIt:setPropertyForPlugin(_PLUGIN, 'face_count', nil)
			ProgressBar:setPortionComplete(i, countPhotos)
		end --end of for photos loop
		ProgressBar:done()
	end, { timeout = TIMEOUT, asynchronous = true }) --end of withPrivateWriteAccessDo
end ) --end of startAsyncTask function()
return
