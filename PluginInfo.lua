--[[-------------------------------------------------------
EvalFocus.lrdevplugin
@file	PluginInfo.lua
@brief	Define plugin manager dialogs at C2Cap.lrplugin
@author	remov-b4-flight
---------------------------------------------------------]]
local LrView = import 'LrView'
local bind = LrView.bind -- a local shortcut for the binding function
local prefs = import 'LrPrefs'.prefsForPlugin()

local PluginInfo = {}

function PluginInfo.startDialog( propertyTable )
	propertyTable.AutoReject = prefs.AutoReject
	propertyTable.RejectRange = prefs.RejectRange
end

function PluginInfo.endDialog( propertyTable ,why )
	prefs.AutoReject = propertyTable.AutoReject
	prefs.RejectRange = propertyTable.RejectRange
end

function PluginInfo.sectionsForTopOfDialog( viewFactory, propertyTable )
	return {
		{
			title = 'EvalFocus',
			synopsis = 'Evaluate image focus',
			bind_to_object = propertyTable,
			viewFactory:row {
				viewFactory:checkbox {title = 'AutoReject', value = bind 'AutoReject',},
				viewFactory:edit_field {title = 'Range(less than)', min = 5, max = 255, width_in_chars = 3, value = bind 'RejectRange',},
			},
		},
	}
end

return PluginInfo
