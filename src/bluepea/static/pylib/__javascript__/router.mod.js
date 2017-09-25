	__nest__ (
		__all__,
		'pylib.router', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var inspector = __init__ (__world__.pylib.inspector);
					var route = function (root) {
						m.route (root, '/inspector', dict ({'/inspector': inspector.Renderer}));
					};
					__pragma__ ('<use>' +
						'pylib.inspector' +
					'</use>')
					__pragma__ ('<all>')
						__all__.inspector = inspector;
						__all__.route = route;
					__pragma__ ('</all>')
				}
			}
		}
	);
