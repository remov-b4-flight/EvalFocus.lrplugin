--[[
EvalImage.lrplugin
@file EvalCrear.lua
@author @remov_b4_flight
]]

local PluginTitle = 'EvalFocus'
local LrApplication = import 'LrApplication'
local LrTasks = import 'LrTasks'
local LrProgress = import 'LrProgressScope'

local CurrentCatalog = LrApplication.activeCatalog()

--Main part of this plugin.
LrTasks.startAsyncTask( function ()
	local ProgressBar = LrProgress(
		{title = PluginTitle .. ' Clearing..'}
	)
	local TargetPhoto = CurrentCatalog:getTargetPhoto()
	local SelectedPhotos = CurrentCatalog:getTargetPhotos()
	local countPhotos = #SelectedPhotos
	--loops photos in selected
	CurrentCatalog:withWriteAccessDo('Evaluate Focus',function()
		for i,PhotoIt in ipairs(SelectedPhotos) do
				PhotoIt:setPropertyForPlugin(_PLUGIN,'accuracy',nil)
				PhotoIt:setPropertyForPlugin(_PLUGIN,'rank',nil)
			ProgressBar:setPortionComplete(i,countPhotos)
		end --end of for photos loop
		ProgressBar:done()
	end ) --end of withWriteAccessDo
end ) --end of startAsyncTask function()
return
