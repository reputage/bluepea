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
					var Entities = __class__ ('Entities', [Tab], {
						Name: 'Entities',
						Data_tab: 'entities',
						Active: true,
						_view: dict ({'view': (function __lambda__ () {
							return m ('div', 'hello Entities');
						})}),
						get main_view () {return __get__ (this, function (self) {
							return m (self._view);
						});}
					});
					var Issuants = __class__ ('Issuants', [Tab], {
						Name: 'Issuants',
						Data_tab: 'issuants'
					});
					var Offers = __class__ ('Offers', [Tab], {
						Name: 'Offers',
						Data_tab: 'offers'
					});
					var Messages = __class__ ('Messages', [Tab], {
						Name: 'Messages',
						Data_tab: 'messages'
					});
					var AnonMsgs = __class__ ('AnonMsgs', [Tab], {
						Name: 'Anon Msgs',
						Data_tab: 'anonmsgs'
					});
					var Tabs = __class__ ('Tabs', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.tabs = list ([Entities (), Issuants (), Offers (), Messages (), AnonMsgs ()]);
							jQuery (document).ready ((function __lambda__ () {
								return jQuery ('.menu .item').tab ();
							}));
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
							return m ('div', m ('div.ui.top.attached.pointing.menu', menu_items), tab_items);
						});}
					});
					var tabs = Tabs ();
					var Renderer = dict ({'render': tabs.view});
					__pragma__ ('<all>')
						__all__.AnonMsgs = AnonMsgs;
						__all__.Entities = Entities;
						__all__.Issuants = Issuants;
						__all__.Messages = Messages;
						__all__.Offers = Offers;
						__all__.Renderer = Renderer;
						__all__.Tab = Tab;
						__all__.Tabs = Tabs;
						__all__.tabs = tabs;
					__pragma__ ('</all>')
				}
			}
		}
	);
