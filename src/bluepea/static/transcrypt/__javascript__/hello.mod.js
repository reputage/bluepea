	(function () {
		var m = require ('mithril');
		m.render (document.body, 'Hello python');
		__pragma__ ('<all>')
			__all__.m = m;
		__pragma__ ('</all>')
	}) ();
