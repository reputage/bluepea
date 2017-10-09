	__nest__ (
		__all__,
		'pylib.inspector', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var server = __init__ (__world__.pylib.server);
					var Tab = __class__ ('Tab', [object], {
						Name: '',
						Data_tab: '',
						Active: false,
						get __init__ () {return __get__ (this, function (self) {
							self._menu_attrs = dict ({'data-tab': self.Data_tab});
							self._tab_attrs = dict ({'data-tab': self.Data_tab});
							self._menu = 'a.item';
							self._tab = 'div.ui.bottom.attached.tab.segment';
							if (self.Active) {
								self._menu += '.active';
								self._tab += '.active';
							}
						});},
						get menu_item () {return __get__ (this, function (self) {
							return m (self._menu, self._menu_attrs, self.Name);
						});},
						get tab_item () {return __get__ (this, function (self) {
							return m (self._tab, self._tab_attrs, self.main_view ());
						});},
						get main_view () {return __get__ (this, function (self) {
							return m ('div', 'hello ' + self.Name);
						});}
					});
					var TabledTab = __class__ ('TabledTab', [Tab], {
						get __init__ () {return __get__ (this, function (self) {
							__super__ (TabledTab, '__init__') (self);
							self.table = null;
							self.setup_table ();
							self.copiedDetails = '';
							self._detailsId = self.Data_tab + 'DetailsCodeBlock';
							self._copiedId = self.Data_tab + 'CopiedCodeBlock';
							self._copyButtonId = self.Data_tab + 'CopyButton';
							self._clearButtonId = self.Data_tab + 'ClearButton';
						});},
						get setup_table () {return __get__ (this, function (self) {
							self.table = Table (list ([]));
						});},
						get _copyDetails () {return __get__ (this, function (self) {
							self.copiedDetails = self.table.detailSelected;
						});},
						get _clearCopy () {return __get__ (this, function (self) {
							self.copiedDetails = '';
						});},
						get main_view () {return __get__ (this, function (self) {
							return m ('div', m ('div.table-container', m (self.table.view)), m ('div.ui.hidden.divider'), m ('div.ui.two.cards', dict ({'style': 'height: 45%;'}), m ('div.ui.card', m ('div.content.small-header', m ('div.header', m ('span', 'Details'), m ('span.ui.mini.right.floated.button', dict ({'onclick': self._copyDetails, 'id': self._copyButtonId}), 'Copy'))), m ('pre.content.code-block', dict ({'id': self._detailsId}), self.table.detailSelected)), m ('div.ui.card', m ('div.content.small-header', m ('div.header', m ('span', 'Copied'), m ('span.ui.mini.right.floated.button', dict ({'onclick': self._clearCopy, 'id': self._clearButtonId}), 'Clear'))), m ('pre.content.code-block', dict ({'id': self._copiedId}), self.copiedDetails))));
						});}
					});
					var Field = __class__ ('Field', [object], {
						Title: null,
						Length: 4,
						get __init__ () {return __get__ (this, function (self, title, length) {
							if (typeof title == 'undefined' || (title != null && title .hasOwnProperty ("__kwargtrans__"))) {;
								var title = null;
							};
							if (typeof length == 'undefined' || (length != null && length .hasOwnProperty ("__kwargtrans__"))) {;
								var length = null;
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'title': var title = __allkwargs0__ [__attrib0__]; break;
											case 'length': var length = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							self.title = self.Title;
							if (title !== null) {
								self.title = title;
							}
							self.mlength = self.Length;
							if (length !== null) {
								self.mlength = length;
							}
							self.py_name = self.title.lower ();
						});},
						get format () {return __get__ (this, function (self, data) {
							return str (data);
						});},
						get shorten () {return __get__ (this, function (self, string) {
							if (len (string) > self.mlength + 3) {
								var string = string.__getslice__ (0, self.mlength, 1) + '...';
							}
							return string;
						});},
						get view () {return __get__ (this, function (self, data) {
							if (data == null) {
								var data = '';
							}
							var formatted = self.format (data);
							return m ('td', dict ({'title': formatted}), self.shorten (formatted));
						});}
					});
					var FillField = __class__ ('FillField', [Field], {
						Length: 100,
						get view () {return __get__ (this, function (self, data) {
							var node = __super__ (FillField, 'view') (self, data);
							node.attrs ['class'] = 'fill-space';
							return node;
						});}
					});
					var DateField = __class__ ('DateField', [Field], {
						Length: 12,
						Title: 'Date'
					});
					var EpochField = __class__ ('EpochField', [DateField], {
						get format () {return __get__ (this, function (self, data) {
							var data = new Date (data / 1000).toISOString ();
							return __super__ (EpochField, 'format') (self, data);
						});}
					});
					var IDField = __class__ ('IDField', [Field], {
						Length: 4,
						Title: 'UID',
						Header: '',
						get format () {return __get__ (this, function (self, string) {
							if (string.startswith (self.Header)) {
								var string = string.__getslice__ (len (self.Header), null, 1);
							}
							return __super__ (IDField, 'format') (self, string);
						});}
					});
					var DIDField = __class__ ('DIDField', [IDField], {
						Header: 'did:igo:',
						Title: 'DID'
					});
					var HIDField = __class__ ('HIDField', [IDField], {
						Header: 'hid:',
						Title: 'HID',
						get shorten () {return __get__ (this, function (self, string) {
							if (len (string) > 13) {
								var string = (string.__getslice__ (0, 6, 1) + '...') + string.__getslice__ (-(4), null, 1);
							}
							return string;
						});}
					});
					var OIDField = __class__ ('OIDField', [IDField], {
						Header: 'o_',
						Title: 'UID'
					});
					var MIDField = __class__ ('MIDField', [IDField], {
						Header: 'm_',
						Title: 'UID'
					});
					var Table = __class__ ('Table', [object], {
						no_results_text: 'No results found.',
						get __init__ () {return __get__ (this, function (self, fields) {
							self.max_size = 1000;
							self.fields = fields;
							self.data = dict ({});
							self.view = dict ({'oninit': self._oninit, 'view': self._view});
							self._selectedRow = null;
							self._selectedUid = null;
							self.detailSelected = '';
							self.filter = null;
							self._nextId = 0;
						});},
						get _stringify () {return __get__ (this, function (self, obj) {
							return JSON.stringify (obj, null, 2);
						});},
						get _limitText () {return __get__ (this, function (self) {
							return 'Limited to {} results.'.format (self.max_size);
						});},
						get _selectRow () {return __get__ (this, function (self, event, uid) {
							if (uid == self._selectedUid) {
								return ;
							}
							self._selectedUid = uid;
							if (self._selectedRow !== null) {
								jQuery (self._selectedRow).removeClass ('active');
							}
							self._selectedRow = event.currentTarget;
							jQuery (self._selectedRow).addClass ('active');
							self.detailSelected = self._stringify (self.data [uid]);
						});},
						get _oninit () {return __get__ (this, function (self) {
							self._setData (list ([]));
						});},
						get _makeDummyData () {return __get__ (this, function (self, count) {
							var data = list ([]);
							for (var i = 0; i < count; i++) {
								var obj = dict ({});
								var __iterable0__ = self.fields;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var field = __iterable0__ [__index0__];
									obj [field.py_name] = 'test{0} {1}'.format (i, field.py_name);
								}
								data.append (obj);
							}
							return data;
						});},
						get _setData () {return __get__ (this, function (self, data, py_clear) {
							if (typeof py_clear == 'undefined' || (py_clear != null && py_clear .hasOwnProperty ("__kwargtrans__"))) {;
								var py_clear = true;
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'data': var data = __allkwargs0__ [__attrib0__]; break;
											case 'py_clear': var py_clear = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							if (py_clear) {
								self._nextId = 0;
								self.data.py_clear ();
							}
							var __iterable0__ = data;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var datum = __iterable0__ [__index0__];
								self.data [self._nextId] = datum;
								self._nextId++;
							}
						});},
						get _makeRow () {return __get__ (this, function (self, obj) {
							return function () {
								var __accu0__ = [];
								var __iterable0__ = self.fields;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var field = __iterable0__ [__index0__];
									__accu0__.append (field.view (obj [field.py_name]));
								}
								return __accu0__;
							} ();
						});},
						get _view () {return __get__ (this, function (self) {
							var headers = function () {
								var __accu0__ = [];
								var __iterable0__ = self.fields;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var field = __iterable0__ [__index0__];
									__accu0__.append (m ('th', field.title));
								}
								return __accu0__;
							} ();
							var rows = list ([]);
							var count = 0;
							var __iterable0__ = self.data.py_items ();
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var __left0__ = __iterable0__ [__index0__];
								var key = __left0__ [0];
								var obj = __left0__ [1];
								if (count >= self.max_size) {
									rows.append (m ('tr', m ('td', self._limitText ())));
									break;
								}
								if (self.filter !== null) {
									if (!(self.filter (obj))) {
										continue;
									}
								}
								var row = self._makeRow (obj);
								var makeScope = function (uid) {
									return (function __lambda__ (event) {
										return self._selectRow (event, uid);
									});
								};
								rows.append (m ('tr', dict ({'onclick': makeScope (key)}), row));
								count++;
							}
							if (!(count)) {
								rows.append (m ('tr', m ('td', self.no_results_text)));
							}
							return m ('table', dict ({'class': 'ui selectable celled unstackable single line left aligned table'}), m ('thead', m ('tr', dict ({'class': 'center aligned'}), headers)), m ('tbody', rows));
						});}
					});
					var AnonMsgsTable = __class__ ('AnonMsgsTable', [Table], {
						get __init__ () {return __get__ (this, function (self) {
							var fields = list ([IDField ('UID'), DateField (), EpochField ('Created'), EpochField ('Expire'), FillField ('Content')]);
							__super__ (AnonMsgsTable, '__init__') (self, fields);
						});},
						get _oninit () {return __get__ (this, function (self) {
							var msgs = server.manager.anonMsgs;
							msgs.refresh ().then ((function __lambda__ () {
								return self._setData (msgs.messages);
							}));
						});},
						get _makeRow () {return __get__ (this, function (self, obj) {
							var row = list ([]);
							var __iterable0__ = self.fields;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var field = __iterable0__ [__index0__];
								if (field.py_name == 'uid') {
									var data = obj.anon.uid;
								}
								else if (field.py_name == 'date') {
									var data = obj.anon.date;
								}
								else if (field.py_name == 'content') {
									var data = obj.anon.content;
								}
								else if (field.py_name == 'created') {
									var data = obj.create;
								}
								else {
									var data = obj [field.py_name];
								}
								row.append (field.view (data));
							}
							return row;
						});}
					});
					var IssuantsTable = __class__ ('IssuantsTable', [Table], {
						get __init__ () {return __get__ (this, function (self) {
							var fields = list ([DIDField (), Field ('Kind'), FillField ('Issuer'), DateField ('Registered'), FillField ('URL')]);
							__super__ (IssuantsTable, '__init__') (self, fields);
						});},
						get _oninit () {return __get__ (this, function (self) {
							var entities = server.manager.entities;
							entities.refreshIssuants ().then ((function __lambda__ () {
								return self._setData (entities.issuants);
							}));
						});},
						get _makeRow () {return __get__ (this, function (self, obj) {
							var row = list ([]);
							var __iterable0__ = self.fields;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var field = __iterable0__ [__index0__];
								if (field.py_name == 'url') {
									var data = obj.validationURL;
								}
								else {
									var data = obj [field.py_name];
								}
								row.append (field.view (data));
							}
							return row;
						});}
					});
					var OffersTable = __class__ ('OffersTable', [Table], {
						get __init__ () {return __get__ (this, function (self) {
							var fields = list ([OIDField ('UID'), DIDField ('Thing'), DIDField ('Aspirant'), Field ('Duration', __kwargtrans__ ({length: 5})), DateField ('Expiration'), DIDField ('Signer'), DIDField ('Offerer')]);
							__super__ (OffersTable, '__init__') (self, fields);
						});},
						get _oninit () {return __get__ (this, function (self) {
							var entities = server.manager.entities;
							entities.refreshOffers ().then ((function __lambda__ () {
								return self._setData (entities.offers);
							}));
						});}
					});
					var MessagesTable = __class__ ('MessagesTable', [Table], {
						get __init__ () {return __get__ (this, function (self) {
							var fields = list ([MIDField ('UID'), Field ('Kind', __kwargtrans__ ({length: 8})), DateField (), DIDField ('To'), DIDField ('From'), DIDField ('Thing'), Field ('Subject', __kwargtrans__ ({length: 10})), FillField ('Content')]);
							__super__ (MessagesTable, '__init__') (self, fields);
						});},
						get _oninit () {return __get__ (this, function (self) {
							var entities = server.manager.entities;
							entities.refreshMessages ().then ((function __lambda__ () {
								return self._setData (entities.messages);
							}));
						});}
					});
					var EntitiesTable = __class__ ('EntitiesTable', [Table], {
						get __init__ () {return __get__ (this, function (self) {
							var fields = list ([DIDField (), HIDField (), DIDField ('Signer'), DateField ('Changed'), Field ('Issuants'), FillField ('Data'), Field ('Keys')]);
							__super__ (EntitiesTable, '__init__') (self, fields);
						});},
						get _oninit () {return __get__ (this, function (self) {
							var entities = server.manager.entities;
							entities.refreshAgents ().then ((function __lambda__ () {
								return self._setData (entities.agents, __kwargtrans__ ({py_clear: false}));
							}));
							entities.refreshThings ().then ((function __lambda__ () {
								return self._setData (entities.things, __kwargtrans__ ({py_clear: false}));
							}));
						});},
						get _makeRow () {return __get__ (this, function (self, obj) {
							var row = list ([]);
							var __iterable0__ = self.fields;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var field = __iterable0__ [__index0__];
								if (field.py_name == 'issuants') {
									var issuants = obj [field.py_name];
									if (issuants) {
										var data = len (issuants);
									}
									else {
										var data = '';
									}
								}
								else if (field.py_name == 'keys') {
									var py_keys = obj [field.py_name];
									if (py_keys) {
										var data = len (py_keys);
									}
									else {
										var data = '';
									}
								}
								else if (field.py_name == 'data') {
									var d = obj [field.py_name];
									if (d && d.keywords && d.message) {
										var data = ' '.join (d.keywords);
										data += ' ' + d.message;
									}
									else {
										var data = '';
									}
								}
								else {
									var data = obj [field.py_name];
								}
								row.append (field.view (data));
							}
							return row;
						});}
					});
					var Entities = __class__ ('Entities', [TabledTab], {
						Name: 'Entities',
						Data_tab: 'entities',
						Active: true,
						get setup_table () {return __get__ (this, function (self) {
							self.table = EntitiesTable ();
						});}
					});
					var Issuants = __class__ ('Issuants', [TabledTab], {
						Name: 'Issuants',
						Data_tab: 'issuants',
						get setup_table () {return __get__ (this, function (self) {
							self.table = IssuantsTable ();
						});}
					});
					var Offers = __class__ ('Offers', [TabledTab], {
						Name: 'Offers',
						Data_tab: 'offers',
						get setup_table () {return __get__ (this, function (self) {
							self.table = OffersTable ();
						});}
					});
					var Messages = __class__ ('Messages', [TabledTab], {
						Name: 'Messages',
						Data_tab: 'messages',
						get setup_table () {return __get__ (this, function (self) {
							self.table = MessagesTable ();
						});}
					});
					var AnonMsgs = __class__ ('AnonMsgs', [TabledTab], {
						Name: 'Anon Msgs',
						Data_tab: 'anonmsgs',
						get setup_table () {return __get__ (this, function (self) {
							self.table = AnonMsgsTable ();
						});}
					});
					var Searcher = __class__ ('Searcher', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.searchTerm = null;
							self.caseSensitive = false;
						});},
						get setSearch () {return __get__ (this, function (self, term) {
							self.searchTerm = term || '';
							self.caseSensitive = self.searchTerm.startswith ('"') && self.searchTerm.endswith ('"');
							if (self.caseSensitive) {
								self.searchTerm = self.searchTerm.__getslice__ (1, -(1), 1);
							}
							else {
								self.searchTerm = self.searchTerm.lower ();
							}
						});},
						get _checkPrimitive () {return __get__ (this, function (self, item) {
							if (isinstance (item, str)) {
								if (!(self.caseSensitive)) {
									var item = item.lower ();
								}
								return __in__ (self.searchTerm, item);
							}
							return false;
						});},
						get _checkAny () {return __get__ (this, function (self, value) {
							if (isinstance (value, dict) || isinstance (value, Object)) {
								return self.search (value);
							}
							else if (isinstance (value, list)) {
								var __iterable0__ = value;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var item = __iterable0__ [__index0__];
									if (self._checkAny (item)) {
										return true;
									}
								}
								return false;
							}
							else {
								return self._checkPrimitive (value);
							}
						});},
						get search () {return __get__ (this, function (self, obj) {
							for (var key in obj) {
								var value = obj [key];
								if (self._checkAny (value)) {
									return true;
								}
							}
							return false;
						});}
					});
					var Tabs = __class__ ('Tabs', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.tabs = list ([Entities (), Issuants (), Offers (), Messages (), AnonMsgs ()]);
							self._searchId = 'inspectorSearchId';
							self.searcher = Searcher ();
							jQuery (document).ready ((function __lambda__ () {
								return jQuery ('.menu > a.item').tab ();
							}));
						});},
						get currentTab () {return __get__ (this, function (self) {
							var active = jQuery ('.menu a.item.active');
							var data_tab = active.attr ('data-tab');
							var __iterable0__ = self.tabs;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var tab = __iterable0__ [__index0__];
								if (tab.Data_tab == data_tab) {
									return tab;
								}
							}
							return null;
						});},
						get search () {return __get__ (this, function (self) {
							var text = jQuery ('#' + self._searchId).val ();
							self.searcher.setSearch (text);
							var current = self.currentTab ();
							var __iterable0__ = self.tabs;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var tab = __iterable0__ [__index0__];
								if (text && tab.Data_tab == current.Data_tab) {
									tab.table.filter = self.searcher.search;
								}
								else {
									tab.table.filter = null;
								}
							}
						});},
						get view () {return __get__ (this, function (self) {
							var menu_items = list ([]);
							var tab_items = list ([]);
							var __iterable0__ = self.tabs;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var tab = __iterable0__ [__index0__];
								menu_items.append (tab.menu_item ());
								tab_items.append (tab.tab_item ());
							}
							return m ('div', m ('form', dict ({'onsubmit': self.search}), m ('div.ui.borderless.menu', m ('div.right.menu', dict ({'style': 'padding-right: 40%'}), m ('div.item', dict ({'style': 'width: 80%'}), m ('div.ui.transparent.icon.input', m ('input[type=text][placeholder=Search...]', dict ({'id': self._searchId})), m ('i.search.icon'))), m ('div.item', m ('input.ui.primary.button[type=submit][value=Search]'))))), m ('div.ui.top.attached.pointing.five.item.menu', menu_items), tab_items);
						});}
					});
					__pragma__ ('<use>' +
						'pylib.server' +
					'</use>')
					__pragma__ ('<all>')
						__all__.AnonMsgs = AnonMsgs;
						__all__.AnonMsgsTable = AnonMsgsTable;
						__all__.DIDField = DIDField;
						__all__.DateField = DateField;
						__all__.Entities = Entities;
						__all__.EntitiesTable = EntitiesTable;
						__all__.EpochField = EpochField;
						__all__.Field = Field;
						__all__.FillField = FillField;
						__all__.HIDField = HIDField;
						__all__.IDField = IDField;
						__all__.Issuants = Issuants;
						__all__.IssuantsTable = IssuantsTable;
						__all__.MIDField = MIDField;
						__all__.Messages = Messages;
						__all__.MessagesTable = MessagesTable;
						__all__.OIDField = OIDField;
						__all__.Offers = Offers;
						__all__.OffersTable = OffersTable;
						__all__.Searcher = Searcher;
						__all__.Tab = Tab;
						__all__.Table = Table;
						__all__.TabledTab = TabledTab;
						__all__.Tabs = Tabs;
						__all__.server = server;
					__pragma__ ('</all>')
				}
			}
		}
	);
