	(function () {
		var root = document.body;
		var test = function () {
			m.render (root, list ([m ('h2', dict ({'class': 'title'}), 'Hello Python Module World'), m ('button', dict ({'class': 'ui button'}), 'Go Python Module')]));
		};
		__pragma__ ('<all>')
			__all__.root = root;
			__all__.test = test;
		__pragma__ ('</all>')
	}) ();
