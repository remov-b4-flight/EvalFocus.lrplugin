--[[
EvalFocus.lrplugin
@file MetadataDefinition.lua
@author @remov_b4_flight
]]

return {
	metadataFieldsForPhotos = {
		{id = 'value', title = 'Value', datatype = 'string', browsable = true, searchable = true, readOnly = true },
		{id = 'rank', title = 'Rank', datatype = 'enum', browsable = true, searchable = true, readOnly = true 
			values = {
				{value = nil, title ='unknown'},
				{value = 'yes', title ='looks good'},
				{value = 'no', title ='rejectable'},
			},
		},
	},
	schemaVersion = 4,
}
