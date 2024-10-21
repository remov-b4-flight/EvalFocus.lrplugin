--[[-------------------------------------------------------
EvalFocus.lrdevplugin
@file	Info.lua
@author	@remov_b4_flight
---------------------------------------------------------]]

return {

	LrSdkVersion = 4.0,

	LrToolkitIdentifier = 'nu.mine.ruffles.evalfocus',
	LrPluginName = 'EvalFocus',
	LrPluginInfoUrl='https://twitter.com/remov_b4_flight',
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
	VERSION = { major = 0, minor = 9, revision = 3, build = 0, },

}
