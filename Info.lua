--[[-------------------------------------------------------
@file	Info.lua
@author	@remov_b4_flight
@brief	all the metadata for the plugin
---------------------------------------------------------]]

return {

	LrSdkVersion = 4.0,

	LrToolkitIdentifier = 'cx.ath.remov-b4-flight.evalfocus',
	LrPluginName = 'EvalFocus',
	LrPluginInfoUrl='https://x.com/remov_b4_flight',
	LrMetadataProvider = 'MetadataDefinition.lua',
	LrPluginInfoProvider = 'PluginInfo.lua',
	LrInitPlugin = 'PluginInit.lua',
	LrLibraryMenuItems = { 
		{title = 'Evaluate',
		file = 'EvalFocus.lua',
		enabledWhen = 'photosAvailable',},
		{title = 'Clear Evaluate',
		file = 'EvalClear.lua',
		enabledWhen = 'photosAvailable',},
	},
	VERSION = { major = 1, minor = 3, revision = 1, build = 182, },
}
