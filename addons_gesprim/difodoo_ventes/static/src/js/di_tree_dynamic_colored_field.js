
odoo.define('difodoo_ventes.di_couleur_col_backend', function (require) {
// The goal of this file is to contain JS hacks related to allowing
// section and note on sale order and invoice.

// [UPDATED] now also allows configuring products on sale order.

"use strict";
var pyUtils = require('web.py_utils');
var core = require('web.core');
var _t = core._t;
var FieldChar = require('web.basic_fields').FieldChar;
var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
var fieldRegistry = require('web.field_registry');
var FieldText = require('web.basic_fields').FieldText;
var ListRenderer = require('web.ListRenderer');

var DiCouleurColListRenderer = ListRenderer.extend({
    /**
     * We want section and note to take the whole line (except handle and trash)
     * to look better and to hide the unnecessary fields.
     *
     * @override
     */
    _renderBodyCell: function (record, node, index, options) {
        window.alert('test1');
        var $cell = this._super.apply(this, arguments);
        $cell.css('background-color', 'Blue');           
        return $cell;
    }
      
});

// We create a custom widget because this is the cleanest way to do it:
// to be sure this custom code will only impact selected fields having the widget
// and not applied to any other existing ListRenderer.
var DiCouleurCol = FieldOne2Many.extend({
    /**
     * We want to use our custom renderer for the list.
     *
     * @override
     */
    _getRenderer: function () {
        window.alert('test2');
        if (this.view.arch.tag === 'tree') {
            return DiCouleurColListRenderer;
        }
        return this._super.apply(this, arguments);
    },
});


fieldRegistry.add('di_couleur_col', DiCouleurCol);

});
