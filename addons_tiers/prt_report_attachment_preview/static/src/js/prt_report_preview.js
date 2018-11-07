odoo.define('prt_report_attachment_preview.ReportPreview', function (require) {
"use strict";

var Session = require('web.Session');
var core = require('web.core');
var QWeb = core.qweb;
var Sidebar = require('web.Sidebar');


// Session
Session.include({

    get_file: function(options) {
      var token = new Date().getTime();
      options.session = this;
      var params = _.extend({}, options.data || {}, {token: token});
      var url = options.session.url(options.url, params);
      if (options.complete) { options.complete(); }

        //impression directe sur l'imprimante par défaut (ou ouverture de la boite de dialogue)
//         var objFra = document.createElement('iframe');   // CREATE AN IFRAME.
//         objFra.style.visibility = "hidden";    // HIDE THE FRAME.
//         objFra.src = url;                      // SET SOURCE.
//         document.body.appendChild(objFra);  // APPEND THE FRAME TO THE PAGE.
//         objFra.contentWindow.focus();       // SET FOCUS.
//         objFra.contentWindow.print();  
      //ouverture du doc dans un nouvel onglet  
      var w = window.open(url);
      if (!w || w.closed || typeof w.closed === 'undefined') {
         //  popup was blocked
          return false;
      }
      return true;
     },
  });

// Sidebar
Sidebar.include({

  _redraw: function () {
    var self = this;
    this._super.apply(this, arguments);
    self.$el.find("a[href]").attr('target', '_blank');
    },
  });

});
