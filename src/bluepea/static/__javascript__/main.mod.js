	(function () {
		var router = __init__ (__world__.pylib.router);
		router.route (document.body);
		__pragma__ ('<use>' +
			'pylib.router' +
		'</use>')
		__pragma__ ('<all>')
			__all__.router = router;
		__pragma__ ('</all>')
	}) ();
