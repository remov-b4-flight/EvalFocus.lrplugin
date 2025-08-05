--[[-------------------------------------------------------
EvalFocus.lrdevplugin
@file MetadataDefinition.lua
@author @remov_b4_flight
-----------------------------------------------------------]]

return {
	metadataFieldsForPhotos = {
		{id = 'value', title = 'Value', datatype = 'string', browsable = true, searchable = true, readOnly = true },
		{id = 'face_count', title = 'Face Count', datatype = 'string', browsable = true, searchable = true, readOnly = true },
	},
	schemaVersion = 4,
}
