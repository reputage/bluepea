	(function () {
		var pylib = {};
		__nest__ (pylib, 'hello', __init__ (__world__.pylib.hello));
		var root = document.body;
		m.render (root, list ([m ('h1', dict ({'class': 'title'}), 'Hello Python World'), m ('button', dict ({'class': 'ui button'}), 'Go Python')]));
		__pragma__ ('<use>' +
			'pylib.hello' +
		'</use>')
		__pragma__ ('<all>')
			__all__.root = root;
		__pragma__ ('</all>')
	}) ();
