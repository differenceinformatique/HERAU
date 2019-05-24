odoo.define('web.di_relational_fields', function (require) {
"use strict";

/**
 * Relational Fields
 *
 * In this file, we have a collection of various relational field widgets.
 * Relational field widgets are more difficult to use/manipulate, because the
 * relations add a level of complexity: a value is not a basic type, it can be
 * a collection of other records.
 *
 * Also, the way relational fields are edited is more complex.  We can change
 * the corresponding record(s), or alter some of their fields.
 */

var AbstractField = require('web.AbstractField');
var FieldMany2One = require('web.FieldMany2One');
var basicFields = require('web.basic_fields');
var concurrency = require('web.concurrency');
var ControlPanel = require('web.ControlPanel');
var dialogs = require('web.view_dialogs');
var core = require('web.core');
var data = require('web.data');
var Dialog = require('web.Dialog');
var KanbanRenderer = require('web.KanbanRenderer');
var ListRenderer = require('web.ListRenderer');
var Pager = require('web.Pager');

var _t = core._t;
var qweb = core.qweb;

/**
 * The FieldReference is a combination of a select (for the model) and
 * a FieldMany2one for its value.
 * Its intern representation is similar to the many2one (a datapoint with a
 * `name_get` as data).
 * Note that there is some logic to support char field because of one use in our
 * codebase, but this use should be removed along with this note.
 */
 
 
var di_FieldMany2One = FieldMany2One.include({
/**
     * @override
     * @param {boolean} [options.noOpen=false] if true, there is no external
     *   button to open the related record in a dialog
     */
    init: function (parent, name, record, options) {
        this._super.apply(this, arguments);
        this.limit = 1;
        this.orderer = new concurrency.DropMisordered();

        // should normally also be set, except in standalone M20
        this.can_create = ('can_create' in this.attrs ? JSON.parse(this.attrs.can_create) : true) &&
            !this.nodeOptions.no_create;
        this.can_write = 'can_write' in this.attrs ? JSON.parse(this.attrs.can_write) : true;

        this.nodeOptions = _.defaults(this.nodeOptions, {
            quick_create: true,
        });
        this.noOpen = 'noOpen' in (options || {}) ? options.noOpen : this.nodeOptions.no_open;
        this.m2o_value = this._formatValue(this.value);
        // 'recordParams' is a dict of params used when calling functions
        // 'getDomain' and 'getContext' on this.record
        this.recordParams = {fieldName: this.name, viewType: this.viewType};
        // We need to know if the widget is dirty (i.e. if the user has changed
        // the value, and those changes haven't been acknowledged yet by the
        // environment), to prevent erasing that new value on a reset (e.g.
        // coming by an onchange on another field)
        this.isDirty = false;
        this.lastChangeEvent = undefined;

        // List of autocomplete sources
        this._autocompleteSources = [];
        // Add default search method for M20 (name_search)
        this._addAutocompleteSource(this._search, {placeholder: _t('Loading...'), order: 1});

        // use a DropPrevious to properly handle related record quick creations,
        // and store a createDef to be able to notify the environment that there
        // is pending quick create operation
        this.dp = new concurrency.DropPrevious();
        this.createDef = undefined;
    },
});
return di_FieldMany2One;

});
