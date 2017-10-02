	__nest__ (
		__all__,
		'pylib.router', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var inspector = __init__ (__world__.pylib.inspector);
					var Router = __class__ ('Router', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.tabs = inspector.Tabs ();
						});},
						get route () {return __get__ (this, function (self, root) {
							if (typeof root == 'undefined' || (root != null && root .hasOwnProperty ("__kwargtrans__"))) {;
								var root = null;
							};
							if (root === null) {
								var root = document.body;
							}
							m.route (root, '/inspector', dict ({'/inspector': dict ({'render': self.tabs.view})}));
						});}
					});
					__pragma__ ('<use>' +
						'pylib.inspector' +
					'</use>')
					__pragma__ ('<all>')
						__all__.Router = Router;
						__all__.inspector = inspector;
					__pragma__ ('</all>')
				}
			}
		}
	);
