	__nest__ (
		__all__,
		'pylib.inspector', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
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
							return m ('div', m ('div.table-container', m (self.table.view)), m ('div.ui.hidden.divider'), m ('div.ui.two.cards', dict ({'style': 'height: 45%;'}), m ('div.ui.card', m ('div.content.small-header', m ('div.header', m ('span', 'Details'), m ('span.ui.mini.right.floated.button', dict ({'onclick': self._copyDetails}), 'Copy'))), m ('pre.content.code-block', self.table.detailSelected)), m ('div.ui.card', m ('div.content.small-header', m ('div.header', m ('span', 'Copied'), m ('span.ui.mini.right.floated.button', dict ({'onclick': self._clearCopy}), 'Clear'))), m ('pre.content.code-block', self.copiedDetails))));
						});}
					});
					var Field = __class__ ('Field', [object], {
						Name: null,
						get __init__ () {return __get__ (this, function (self, py_name) {
							if (typeof py_name == 'undefined' || (py_name != null && py_name .hasOwnProperty ("__kwargtrans__"))) {;
								var py_name = null;
							};
							self.py_name = self.Name;
							if (py_name !== null) {
								self.py_name = py_name;
							}
						});},
						get format () {return __get__ (this, function (self, string) {
							if (len (string) > 8) {
								var string = string.__getslice__ (0, 5, 1) + '...';
							}
							return string;
						});},
						get view () {return __get__ (this, function (self, data) {
							return m ('td', dict ({'title': data}), self.format (data));
						});}
					});
					var Table = __class__ ('Table', [object], {
						get __init__ () {return __get__ (this, function (self, fields) {
							self.max_size = 8;
							self.fields = fields;
							self.data = dict ({});
							self.view = dict ({'oninit': self._oninit, 'view': self._view});
							self._selectedRow = null;
							self._selectedUid = null;
							self.detailSelected = '';
							self.filter = null;
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
							self.detailSelected = JSON.stringify (self.data [uid], null, 2);
						});},
						get _oninit () {return __get__ (this, function (self) {
							for (var i = 0; i < 20; i++) {
								var obj = dict ({});
								var __iterable0__ = self.fields;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var field = __iterable0__ [__index0__];
									obj [field.py_name] = 'test{0} {1}'.format (i, field.py_name);
								}
								self.data [i] = obj;
							}
						});},
						get _view () {return __get__ (this, function (self) {
							var headers = function () {
								var __accu0__ = [];
								var __iterable0__ = self.fields;
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var field = __iterable0__ [__index0__];
									__accu0__.append (m ('th', field.py_name));
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
									rows.append (m ('tr', m ('td', 'Limited to {} results.'.format (self.max_size))));
									break;
								}
								if (self.filter !== null) {
									if (!(self.filter (obj))) {
										continue;
									}
								}
								var row = function () {
									var __accu0__ = [];
									var __iterable1__ = self.fields;
									for (var __index1__ = 0; __index1__ < __iterable1__.length; __index1__++) {
										var field = __iterable1__ [__index1__];
										__accu0__.append (field.view (obj [field.py_name]));
									}
									return __accu0__;
								} ();
								var makeScope = function (uid) {
									return (function __lambda__ (event) {
										return self._selectRow (event, uid);
									});
								};
								rows.append (m ('tr', dict ({'onclick': makeScope (key)}), row));
								count++;
							}
							if (!(count)) {
								rows.append (m ('tr', m ('td', 'No results found.')));
							}
							return m ('table', dict ({'class': 'ui selectable celled unstackable single line left aligned table'}), m ('thead', m ('tr', dict ({'class': 'center aligned'}), headers)), m ('tbody', rows));
						});}
					});
					var Entities = __class__ ('Entities', [TabledTab], {
						Name: 'Entities',
						Data_tab: 'entities',
						Active: true,
						get setup_table () {return __get__ (this, function (self) {
							var fields = function () {
								var __accu0__ = [];
								var __iterable0__ = list (['DID', 'HID', 'Signer', 'Changed', 'Issuants', 'Data', 'Keys']);
								for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
									var x = __iterable0__ [__index0__];
									__accu0__.append (Field (x));
								}
								return __accu0__;
							} ();
							self.table = Table (fields);
						});}
					});
					var Issuants = __class__ ('Issuants', [TabledTab], {
						Name: 'Issuants',
						Data_tab: 'issuants'
					});
					var Offers = __class__ ('Offers', [TabledTab], {
						Name: 'Offers',
						Data_tab: 'offers'
					});
					var Messages = __class__ ('Messages', [TabledTab], {
						Name: 'Messages',
						Data_tab: 'messages'
					});
					var AnonMsgs = __class__ ('AnonMsgs', [TabledTab], {
						Name: 'Anon Msgs',
						Data_tab: 'anonmsgs'
					});
					var Searcher = __class__ ('Searcher', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.searchTerm = null;
							self.caseSensitive = false;
						});},
						get setSearch () {return __get__ (this, function (self, term) {
							self.searchTerm = term;
							self.caseSensitive = term.startswith ('"') && term.endswith ('"');
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
							if (isinstance (value, dict)) {
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
							var __iterable0__ = obj.py_values ();
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var value = __iterable0__ [__index0__];
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
						get search () {return __get__ (this, function (self) {
							var text = jQuery ('#' + self._searchId).val ();
							var currentTab = jQuery ('.menu a.item.active');
							var data_tab = currentTab.attr ('data-tab');
							self.searcher.setSearch (text);
							var __iterable0__ = self.tabs;
							for (var __index0__ = 0; __index0__ < __iterable0__.length; __index0__++) {
								var tab = __iterable0__ [__index0__];
								if (text && tab.Data_tab == data_tab) {
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
					var tabs = Tabs ();
					var Renderer = dict ({'render': tabs.view});
					__pragma__ ('<all>')
						__all__.AnonMsgs = AnonMsgs;
						__all__.Entities = Entities;
						__all__.Field = Field;
						__all__.Issuants = Issuants;
						__all__.Messages = Messages;
						__all__.Offers = Offers;
						__all__.Renderer = Renderer;
						__all__.Searcher = Searcher;
						__all__.Tab = Tab;
						__all__.Table = Table;
						__all__.TabledTab = TabledTab;
						__all__.Tabs = Tabs;
						__all__.tabs = tabs;
					__pragma__ ('</all>')
				}
			}
		}
	);
