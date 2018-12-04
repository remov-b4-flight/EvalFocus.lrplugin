--[[
Info.lua
EvalFocus.lrplugin
Author:@jenoki48
]]

return {

	LrSdkVersion = 3.0,

	LrToolkitIdentifier = 'nu.mine.ruffles.evalfocus',
	LrPluginName = 'EvalFocus',
	LrPluginInfoUrl='https://twitter.com/remov_b4_flight',
	LrMetadataProvider = 'MetadataDefinition.lua',
	LrLibraryMenuItems = { 
		{title = 'Evaluate Face focus',
		file = 'EvalFocus.lua',
		enabledWhen = 'photosAvailable',},
	},
	VERSION = { major=0, minor=0, revision=1, build=0, },

}
