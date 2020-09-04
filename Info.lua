--[[
Info.lua
EvalFocus.lrplugin
Author:@remov_b4_flight
]]

return {

	LrSdkVersion = 3.0,

	LrToolkitIdentifier = 'nu.mine.ruffles.evalfocus',
	LrPluginName = 'EvalFocus',
	LrPluginInfoUrl='https://twitter.com/remov_b4_flight',
	LrMetadataProvider = 'MetadataDefinition.lua',
	LrLibraryMenuItems = { 
		{title = 'Evaluate',
		file = 'EvalFocus.lua',
		enabledWhen = 'photosAvailable',},
	},
	VERSION = { major=0, minor=3, revision=0, build=0, },

}
