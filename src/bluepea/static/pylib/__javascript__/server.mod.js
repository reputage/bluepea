	__nest__ (
		__all__,
		'pylib.server', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var request = function (path) {
						var kwargs = dict ();
						if (arguments.length) {
							var __ilastarg0__ = arguments.length - 1;
							if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
								var __allkwargs0__ = arguments [__ilastarg0__--];
								for (var __attrib0__ in __allkwargs0__) {
									switch (__attrib0__) {
										case 'path': var path = __allkwargs0__ [__attrib0__]; break;
										default: kwargs [__attrib0__] = __allkwargs0__ [__attrib0__];
									}
								}
								delete kwargs.__kwargtrans__;
							}
						}
						else {
						}
						path += '?';
						var __iterable0__ = kwargs.py_items ();
						for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
							var __left0__ = __iterable0__ [__index0__];
							var key = __left0__ [0];
							var value = __left0__ [1];
							path += ((key + '=') + str (value)) + '&';
						}
						var path = path.__getslice__ (0, -(1), 1);
						return m.request (path);
					};
					var onlyOne = function (func, interval) {
						if (typeof interval == 'undefined' || (interval != null && interval .hasOwnProperty ("__kwargtrans__"))) {;
							var interval = 1000;
						};
						if (arguments.length) {
							var __ilastarg0__ = arguments.length - 1;
							if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
								var __allkwargs0__ = arguments [__ilastarg0__--];
								for (var __attrib0__ in __allkwargs0__) {
									switch (__attrib0__) {
										case 'func': var func = __allkwargs0__ [__attrib0__]; break;
										case 'interval': var interval = __allkwargs0__ [__attrib0__]; break;
									}
								}
							}
						}
						else {
						}
						var scope = dict ({'promise': null, 'lastCalled': 0});
						var wrap = function () {
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
									}
								}
							}
							else {
							}
							var now = new Date ();
							if (scope.promise != null && now - scope.lastCalled < interval) {
								return scope.promise;
							}
							scope.lastCalled = now;
							var f = function (resolve, reject) {
								if (arguments.length) {
									var __ilastarg0__ = arguments.length - 1;
									if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
										var __allkwargs0__ = arguments [__ilastarg0__--];
										for (var __attrib0__ in __allkwargs0__) {
											switch (__attrib0__) {
												case 'resolve': var resolve = __allkwargs0__ [__attrib0__]; break;
												case 'reject': var reject = __allkwargs0__ [__attrib0__]; break;
											}
										}
									}
								}
								else {
								}
								var p = func ();
								p.then (resolve);
								p.catch (reject);
							};
							scope.promise = new Promise (f);
							return scope.promise;
						};
						return wrap;
					};
					var clearArray = function (a) {
						while (len (a)) {
							a.py_pop ();
						}
					};
					var Manager = __class__ ('Manager', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.anonMsgs = AnonMessages ();
							self.entities = Entities ();
						});}
					});
					var Entities = __class__ ('Entities', [object], {
						Refresh_Interval: 1000,
						get __init__ () {return __get__ (this, function (self) {
							self.agents = list ([]);
							self.things = list ([]);
							self.issuants = list ([]);
							self.offers = list ([]);
							self.messages = list ([]);
							self.refreshAgents = onlyOne (self._refreshAgents, __kwargtrans__ ({interval: self.Refresh_Interval}));
							self.refreshThings = onlyOne (self._refreshThings, __kwargtrans__ ({interval: self.Refresh_Interval}));
							self.refreshIssuants = self.refreshAgents;
							self.refreshOffers = self.refreshThings;
							self.refreshMessages = self.refreshAgents;
						});},
						get _refreshAgents () {return __get__ (this, function (self) {
							clearArray (self.agents);
							clearArray (self.issuants);
							clearArray (self.messages);
							return request ('/agent', __kwargtrans__ ({all: true})).then (self._parseAllAgents);
						});},
						get _parseAllAgents () {return __get__ (this, function (self, dids) {
							var promises = list ([]);
							var __iterable0__ = dids;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var did = __iterable0__ [__index0__];
								promises.append (request ('/agent', __kwargtrans__ ({did: did})).then (self._parseOneAgent));
								var makeScope = function (did) {
									return (function __lambda__ (data) {
										return self._parseDIDMessages (did, data);
									});
								};
								promises.append (request (('/agent/' + str (did)) + '/drop', __kwargtrans__ ({all: true})).then (makeScope (did)));
							}
							return Promise.all (promises);
						});},
						get _parseOneAgent () {return __get__ (this, function (self, data) {
							if (data.issuants && len (data.issuants) > 0) {
								var __iterable0__ = data.issuants;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var i = __iterable0__ [__index0__];
									var issuant = jQuery.extend (true, dict ({}), i);
									issuant.did = data.did;
									self.issuants.append (issuant);
								}
							}
							self.agents.append (data);
						});},
						get _parseDIDMessages () {return __get__ (this, function (self, did, data) {
							var promises = list ([]);
							var __iterable0__ = data;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var messagestub = __iterable0__ [__index0__];
								promises.append (request (('/agent/' + str (did)) + '/drop', __kwargtrans__ (dict ({'from': messagestub ['from'], 'uid': messagestub.uid}))).then (self._parseDIDMessage));
							}
							return Promise.all (promises);
						});},
						get _parseDIDMessage () {return __get__ (this, function (self, data) {
							self.messages.append (data);
						});},
						get _refreshThings () {return __get__ (this, function (self) {
							clearArray (self.things);
							clearArray (self.offers);
							return request ('/thing', __kwargtrans__ ({all: true})).then (self._parseAllThings);
						});},
						get _parseAllThings () {return __get__ (this, function (self, dids) {
							var promises = list ([]);
							var __iterable0__ = dids;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var did = __iterable0__ [__index0__];
								promises.append (request ('/thing', __kwargtrans__ ({did: did})).then (self._parseOneThing));
								var makeScope = function (did) {
									return (function __lambda__ (data) {
										return self._parseDIDOffers (did, data);
									});
								};
								promises.append (request (('/thing/' + str (did)) + '/offer', __kwargtrans__ ({all: true})).then (makeScope (did)));
							}
							return Promise.all (promises);
						});},
						get _parseOneThing () {return __get__ (this, function (self, data) {
							self.things.append (data);
						});},
						get _parseDIDOffers () {return __get__ (this, function (self, did, data) {
							var promises = list ([]);
							var __iterable0__ = data;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var offerstub = __iterable0__ [__index0__];
								promises.append (request (('/thing/' + str (did)) + '/offer', __kwargtrans__ ({uid: offerstub.uid})).then (self._parseDIDOffer));
							}
							return Promise.all (promises);
						});},
						get _parseDIDOffer () {return __get__ (this, function (self, data) {
							self.offers.append (data);
						});}
					});
					var AnonMessages = __class__ ('AnonMessages', [object], {
						Refresh_Interval: Entities.Refresh_Interval,
						get __init__ () {return __get__ (this, function (self) {
							self.messages = list ([]);
							self.refresh = onlyOne (self._refresh, __kwargtrans__ ({interval: self.Refresh_Interval}));
						});},
						get _refresh () {return __get__ (this, function (self) {
							clearArray (self.messages);
							return request ('/anon', __kwargtrans__ ({all: true})).then (self._parseAll);
						});},
						get _parseAll () {return __get__ (this, function (self, uids) {
							var promises = list ([]);
							var __iterable0__ = uids;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var uid = __iterable0__ [__index0__];
								promises.append (request ('/anon', __kwargtrans__ ({uid: uid})).then (self._parseOne));
							}
							return Promise.all (promises);
						});},
						get _parseOne () {return __get__ (this, function (self, messages) {
							var __iterable0__ = messages;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var message = __iterable0__ [__index0__];
								self.messages.append (message);
							}
						});}
					});
					var manager = Manager ();
					__pragma__ ('<all>')
						__all__.AnonMessages = AnonMessages;
						__all__.Entities = Entities;
						__all__.Manager = Manager;
						__all__.clearArray = clearArray;
						__all__.manager = manager;
						__all__.onlyOne = onlyOne;
						__all__.request = request;
					__pragma__ ('</all>')
				}
			}
		}
	);
