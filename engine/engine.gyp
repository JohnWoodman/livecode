{
	'includes':
	[
		'../common.gypi',
		'engine-sources.gypi',
		'kernel.gypi',
		'kernel-development.gypi',
		'kernel-installer.gypi',
		'kernel-standalone.gypi',
		'kernel-server.gypi',
	],
	
	'target_defaults':
	{
		'conditions':
		[
			[
				'OS == "linux" or OS == "android"',
				{
					# Ensure that the symbols LCB binds to are exported from the engine
					'ldflags': [ '-rdynamic' ],
				},
			],
		],
	},
	
	'targets':
	[
		{
			'target_name': 'encode_version',
			'type': 'none',
			
			'actions':
			[
				{
					'action_name': 'encode_version',
					'inputs':
					[
						'../util/encode_version.pl',
						'../version',
						'include/revbuild.h.in',
					],
					'outputs':
					[
						'<(SHARED_INTERMEDIATE_DIR)/include/revbuild.h',
					],
					
					'action':
					[
						'<@(perl)',
						'../util/encode_version.pl',
						'.',
						'<(SHARED_INTERMEDIATE_DIR)',
					],
				},
			],
			
			'direct_dependent_settings':
			{
				'include_dirs':
				[
					'<(SHARED_INTERMEDIATE_DIR)/include',
				],
			},
		},
		
		{
			'target_name': 'quicktime_stubs',
			'type': 'none',
			
			'actions':
			[
				{
					'action_name': 'quicktime_stubs',
					'inputs':
					[
						'../util/weak_stub_maker.pl',
						'src/quicktime.stubs',
					],
					'outputs':
					[
						'<(SHARED_INTERMEDIATE_DIR)/src/quicktimestubs.mac.cpp',
					],
					
					'action':
					[
						'<@(perl)',
						'../util/weak_stub_maker.pl',
						'src/quicktime.stubs',
						'<@(_outputs)',
					],
				},
			],
		},
		
		{
			'target_name': 'encode_environment_stack',
			'type': 'none',
			
			'actions':
			[
				{
					'action_name': 'encode_environment_stack',
					'inputs':
					[
						'../util/compress_data.pl',
						'src/Environment.rev',
					],
					'outputs':
					[
						'<(SHARED_INTERMEDIATE_DIR)/src/startupstack.cpp',
					],
					
					'action':
					[
						'<@(perl)',
						'../util/compress_data.pl',
						'src/Environment.rev',
						'<@(_outputs)',
						# Really nasty hack to prevent this from being treated as a path
						'$(this_is_an_undefined_variable)MCstartupstack',
					],
				},
			],
		},
		
		{
			'target_name': 'security-community',
			'type': 'static_library',
			
			'dependencies':
			[
				'../thirdparty/libopenssl/libopenssl.gyp:libopenssl',
				
				# Because our headers are so messed up...
				'../libfoundation/libfoundation.gyp:libFoundation',
				'../libgraphics/libgraphics.gyp:libGraphics',
			],
			
			'sources':
			[
				'<@(engine_security_source_files)',
			],
		},
		
		{
			'target_name': 'server',
			'type': 'executable',
			'product_name': 'server-community',
			
			'dependencies':
			[
				'kernel-server',
				
				'../libfoundation/libfoundation.gyp:libFoundation',
				'../libgraphics/libgraphics.gyp:libGraphics',
			],
			
			'sources':
			[
				'<@(engine_security_source_files)',
			],
			
			'conditions':
			[
				[
					'mobile != 0',
					{
						'type': 'none',
						'mac_bundle': 0,
					},
				],
			],
			
			'msvs_settings':
			{
				'VCLinkerTool':
				{
					'SubSystem': '1',	# /SUBSYSTEM:CONSOLE
				},
			},
			
			'all_dependent_settings':
			{
				'variables':
				{
					'dist_files': [ '<(PRODUCT_DIR)/<(_product_name)>(exe_suffix)' ],
				},
			},
		},
		
		{
			'target_name': 'standalone',
			'product_name': 'standalone-community',
			
			'includes':
			[
				'app-bundle-template.gypi',
			],
			
			'variables':
			{
				'app_plist': 'rsrc/Standalone-Info.plist',
			},
			
			'dependencies':
			[
				'kernel-standalone',
				'security-community',
			],
			
			'sources':
			[
				'src/dummy.cpp',
				'rsrc/standalone.rc',
			],
			
			'conditions':
			[
				[
					'OS == "mac"',
					{
						'product_name': 'Standalone-Community',
						'mac_bundle_resources':
						[
							'rsrc/Standalone.icns',
							'rsrc/StandaloneDoc.icns',
						],
					},
				],
				[
					'OS == "ios"',
					{
						'product_name': 'standalone-mobile-lib-community',
						'product_prefix': '',
						'product_extension': 'lcext',
						'app_plist': 'rsrc/standalone-mobile-Info.plist',
						
						# Forces all dependencies to be linked properly
						'type': 'shared_library',
						
						'variables':
						{
							'deps_file': '${SRCROOT}/standalone.ios',
						},

						'xcode_settings':
						{
							'DEAD_CODE_STRIPPING': 'NO',
							'DYLIB_COMPATIBILITY_VERSION': '',
							'DYLIB_CURRENT_VERSION': '',
							'MACH_O_TYPE': 'mh_object',
							'LINK_WITH_STANDARD_LIBRARIES': 'NO',
							'OTHER_LDFLAGS':
							[
								'-Wl,-sectcreate,__MISC,__deps,<(deps_file)',
								'-Wl,-u,_main',
								'-Wl,-u,_load_module',
								'-Wl,-u,_resolve_symbol',
								#'-all_load',		# Dead stripping later will remove un-needed symbols
							],
						},
					},
				],
				[
					# Use a linker script to add the project and payload sections to the Linux executable
					'OS == "linux"',
					{
						'ldflags':
						[
							'-T', '<(src_top_dir_abs)/engine/linux.link',
						],
					},
				],
				[
					# On Android, this needs to be built as a shared library
					'OS == "android"',
					{
						'product_name': 'Standalone-Community',
						'product_prefix': '',
						'product_extension': '',
						'product_dir': '<(PRODUCT_DIR)',	# Shared libraries are not placed in PRODUCT_DIR by default
						'type': 'shared_library',
						
						'ldflags':
						[
							# Helpful for catching build problems
							'-Wl,-no-undefined',
							
							'-Wl,-T,<(src_top_dir_abs)/engine/linux.link',
						],
						
						'actions':
						[
							{
								'action_name': 'copy_manifest',
								'message': 'Copying manifest file',
								
								'inputs':
								[
									'rsrc/android-manifest.xml',
								],
								
								'outputs':
								[
									'<(PRODUCT_DIR)/Manifest.xml',
								],
								
								'action':
								[
									'cp', '<@(_inputs)', '<@(_outputs)',
								],
							},
							{
								'action_name': 'copy_inputcontrol',
								'message': 'Copying input control file',
								
								'inputs':
								[
									'rsrc/android-inputcontrol.xml',
								],
								
								'outputs':
								[
									'<(PRODUCT_DIR)/livecode_inputcontrol.xml',
								],
								
								'action':
								[
									'cp', '<@(_inputs)', '<@(_outputs)',
								],
							},
							{
								'action_name': 'copy_notify_icon',
								'message': 'Copying notification icon',
								
								'inputs':
								[
									'rsrc/android-notify-icon.png'
								],
								
								'outputs':
								[
									'<(PRODUCT_DIR)/notify_icon.png',
								],
								
								'action':
								[
									'cp', '<@(_inputs)', '<@(_outputs)',
								],
							},
						],
						
						'all_dependent_settings':
						{
							'variables':
							{
								'dist_aux_files':
								[
									'<(PRODUCT_DIR)/Manifest.xml',
									'<(PRODUCT_DIR)/livecode_inputcontrol.xml',
									'<(PRODUCT_DIR)/notify_icon.png',
								],
							},
						},
					},
				],
				[
					'OS == "win"',
					{
						'all_dependent_settings':
						{
							'variables':
							{
								'dist_aux_files':
								[
									'rsrc/w32-manifest-template.xml',
									'rsrc/w32-manifest-template-dpiaware.xml',
									'rsrc/w32-manifest-template-trustinfo.xml',
								],
							},
						},
					},
				],
				[
					'OS == "ios"',
					{
						'all_dependent_settings':
						{
							'variables':
							{
								'dist_aux_files':
								[
									'rsrc/Default-568h@2x.png',
									'rsrc/fontmap',
									'rsrc/mobile-device-template.plist',
									'rsrc/mobile-remote-notification-template.plist',
									'rsrc/mobile-splashscreen-template.plist',
									'rsrc/mobile-template.plist',
									'rsrc/mobile-url-scheme-template.plist',
									'rsrc/template-entitlements.xcent',
									'rsrc/template-store-entitlements.xcent',
									'rsrc/template-remote-notification-entitlements.xcent',
									'rsrc/template-remote-notification-store-entitlements.xcent',
									'rsrc/template-ResourceRules.plist',
								],
							},
						},
					},
				],
				[
					'OS == "emscripten"',
					{
						'product_name': 'standalone-community.bc',
						'all_dependent_settings':
						{
							'variables':
							{
								'dist_aux_files':
								[
									'rsrc/emscripten-standalone-template/',
									'<(PRODUCT_DIR)/standalone-community-<(version_string).js',
									'<(PRODUCT_DIR)/standalone-community-<(version_string).html',
									'<(PRODUCT_DIR)/standalone-community-<(version_string).html.mem',
								],
							},
						},

						'sources!':
						[
							'src/dummy.cpp',
						],
					},
				],
			],
			
			'all_dependent_settings':
			{
				'variables':
				{
					'conditions':
					[
						[
							'OS == "android"',
							{
								'dist_files': [ '<(PRODUCT_DIR)/<(_product_name)>(lib_suffix)' ],
							},
						],
						[
							'OS == "ios"',
							{
								'dist_files': [ '<(PRODUCT_DIR)/standalone-mobile-community.ios-engine' ],
							},
						],
						[
							'OS == "emscripten"',
							{
								'dist_files': [],
							}
						],
						[
							'OS != "android" and OS != "ios" and OS != "emscripten"',
							{
								'dist_files': [ '<(PRODUCT_DIR)/<(_product_name)>(app_bundle_suffix)' ],
							}
						],
					],
				},
			},
		},
		
		{
			'target_name': 'installer',
			'product_name': 'installer',
			
			'includes':
			[
				'app-bundle-template.gypi',
			],
			
			'variables':
			{
				'app_plist': 'rsrc/Installer-Info.plist',
			},
			
			'dependencies':
			[
				'kernel-installer',
				'security-community',
			],
			
			'sources':
			[
				'src/dummy.cpp',
				'rsrc/installer.rc',
			],
			
			'conditions':
			[
				[
					'OS == "mac"',
					{
						'product_name': 'Installer',
						'mac_bundle_resources':
						[
							'rsrc/Installer.icns',
						],
					},
				],
				[
					'mobile != 0',
					{
						'type': 'none',
						'mac_bundle': 0,
					},
				],
				[
					# Use a linker script to add the project and payload sections to the Linux executable
					'OS == "linux"',
					{
						'ldflags':
						[
							'-T', '<(src_top_dir_abs)/engine/linux.link',
						],
					},
				],
			],
			
			'msvs_settings':
			{
				'VCManifestTool':
				{
					'AdditionalManifestFiles': '$(ProjectDir)..\\..\\..\\engine\\src\\installer.manifest',
				},
			},
			
			'all_dependent_settings':
			{
				'variables':
				{
					'dist_files': [ '<(PRODUCT_DIR)/<(_product_name)>(app_bundle_suffix)' ],
				},
			},
		},
		
		{
			'target_name': 'development-postprocess',
			'type': 'none',

			'dependencies':
			[
				'development',
				'../thirdparty/libopenssl/libopenssl.gyp:revsecurity',
			],

			'conditions':
			[
				[
					'OS == "mac"',
					{
						'copies':
						[
							{
								'destination': '<(PRODUCT_DIR)/LiveCode-Community.app/Contents/MacOS',
								'files':
								[
									'<(PRODUCT_DIR)/revsecurity.dylib',
								],
							},
						],
					},
				],
			],
		},

		{
			'target_name': 'development',
			'product_name': 'LiveCode-Community',

			'includes':
			[
				'app-bundle-template.gypi',
			],
			
			'variables':
			{
				'app_plist': 'rsrc/Revolution-Info.plist',
			},
			
			'dependencies':
			[
				'kernel-development',
				'encode_environment_stack',
				'security-community',
			],
			
			'sources':
			[
				'<(SHARED_INTERMEDIATE_DIR)/src/startupstack.cpp',
				'rsrc/development.rc',
			],

			'conditions':
			[
				[
					'OS == "mac"',
					{
						'mac_bundle_resources':
						[
							'rsrc/LiveCode.icns',
							'rsrc/LiveCodeDoc.icns',
						],
					},
				],
				[
					'mobile != 0',
					{
						'type': 'none',
						'mac_bundle': 0,
					},
				],
			],
			
			'msvs_settings':
			{
				'VCManifestTool':
				{
					'AdditionalManifestFiles': '$(ProjectDir)..\\..\\..\\engine\\src\\engine.manifest',
				},
			},
			
			# Visual Studio debugging settings
			'run_as':
			{
				'action': [ '<(PRODUCT_DIR)/<(_product_name).exe' ],
				'environment':
				{
					'REV_TOOLS_PATH' : '$(ProjectDir)..\\..\\..\\ide',
				},
			},
			
			'all_dependent_settings':
			{
				'variables':
				{
					'dist_files': [ '<(PRODUCT_DIR)/<(_product_name)>(app_bundle_suffix)' ],
				},
			},
		},
		
		{
			'target_name': 'ios-standalone-executable',
			'type': 'none',
			
			'dependencies':
			[
				'standalone',
			],
			
			'conditions':
			[
				[
					'OS == "ios"',
					{
						'actions':
						[
							{
								'action_name': 'bind-output',
								'message': 'Bind output',
								
								'inputs':
								[
									'<(PRODUCT_DIR)/standalone-mobile-lib-community.lcext',
								],
								
								'outputs':
								[
									'<(PRODUCT_DIR)/standalone-mobile-community.ios-engine',
								],
								
								'action':
								[
									'./bind-ios-standalone.sh',
									'<@(_inputs)',
									'<@(_outputs)',
								],
							},
						],
					},
				],
			],
		},
	],
	
	'conditions':
	[
		[
			'OS == "linux"',
			{
				'targets':
				[
					{
						'target_name': 'create_linux_stubs',
						'type': 'none',
												
						'actions':
						[
							{
								'action_name': 'linux_library_stubs',
								'inputs':
								[
									'../util/weak_stub_maker.pl',
									'src/linux.stubs',
								],
								'outputs':
								[
									'<(SHARED_INTERMEDIATE_DIR)/src/linux.stubs.cpp',
								],
								
								'action':
								[
									'<@(perl)',
									'../util/weak_stub_maker.pl',
									'src/linux.stubs',
									'<@(_outputs)',
								],
							},
						],
					},
				],
			}
		],
		[
			'OS == "ios"',
			{
				'targets':
				[
					{
						'target_name': 'standalone-app-bundle',
						'product_name': 'Standalone-Community-App',
			
						'includes':
						[
							'app-bundle-template.gypi',
						],
			
						'variables':
						{
							'app_plist': 'rsrc/standalone-mobile-Info.plist',
						},
			
						'dependencies':
						[
							'kernel-standalone',
							'security-community',
						],
			
						'sources':
						[
							'src/dummy.cpp',
						],
					},
				],
			},
		],
		[
			'OS == "emscripten"',
			{
				'targets':
				[
					{
						'target_name': 'javascriptify',
						'type': 'none',

						'dependencies':
						[
							'standalone',
						],

						'variables':
						{
							'version_suffix': '<(version_string)',
						},

						'actions':
						[
							{
								'action_name': 'javascriptify',
								'message': 'Javascript-ifying the Emscripten engine',

								'inputs':
								[
									'emscripten-javascriptify.sh',
									'<(PRODUCT_DIR)/standalone-community.bc',
									'src/em-whitelist.json',
									'src/em-preamble.js',
									'src/em-util.js',
									'src/em-async.js',
									'src/em-dialog.js',
									'src/em-event.js',
									'src/em-surface.js',
									'src/em-url.js',
									'src/em-standalone.js',
								],

								'outputs':
								[
									'<(PRODUCT_DIR)/standalone-community-<(version_suffix).js',
									'<(PRODUCT_DIR)/standalone-community-<(version_suffix).html',
									'<(PRODUCT_DIR)/standalone-community-<(version_suffix).html.mem',
								],

								'action':
								[
									'./emscripten-javascriptify.sh',
									'<(PRODUCT_DIR)/standalone-community.bc',
									'<(PRODUCT_DIR)/standalone-community-<(version_suffix).html',
									'src/em-whitelist.json',
									'src/em-preamble.js',
									'src/em-util.js',
									'src/em-async.js',
									'src/em-dialog.js',
									'src/em-event.js',
									'src/em-surface.js',
									'src/em-url.js',
									'src/em-standalone.js',
								],
							},
						],
					},
				],
			},
		],
	],
}
