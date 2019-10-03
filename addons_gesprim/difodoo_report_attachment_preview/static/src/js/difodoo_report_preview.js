odoo.define('difodoo_report_attachment_preview.ReportPreview', function(require) {
    "use strict";

    var Session = require('web.Session');
    var core = require('web.core');
    var QWeb = core.qweb;
    var Sidebar = require('web.Sidebar');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    // Session
    Session.include({

        get_file: function(options) {
        
            var token = require('web.core').csrf_token;
            //var token = new Date().getTime();
            options.session = this;
            var self = this;
            var params = _.extend({}, options.data || {}, {
                token: token
            });

            var url = options.session.url(options.url, params);
            if (options.complete) {
                options.complete();
            }
            if (url.length < 10000){
                return rpc.query({
                    model: 'di.param',
                    method: 'di_get_option_impression',
                    args: [{}]
                }).then(function(result) {                                                                                
                    if (result === 'ONG') { // contrôle du retour de la fonction          
                    //ouverture du doc dans un nouvel onglet            
                        var w = window.open(url);
                        if (!w || w.closed || typeof w.closed === 'undefined') {
                            //  popup was blocked
                            return false;
                        }
                        return true;
                    }
                    if (result === 'STD') { // contrôle du retour de la fonction
                        if (this.override_session) {
                            options.data.session_id = this.session_id;
                        }
                        options.session = this;
                        return ajax.get_file(options);
                    }
                    if (result === 'DIR') { // contrôle du retour de la fonction                                            
                        //impression directe sur l'imprimante par défaut (ou ouverture de la boite de dialogue)
                        var objFra = document.createElement('iframe'); // CREATE AN IFRAME.
                        objFra.style.visibility = "hidden"; // HIDE THE FRAME.
                        objFra.src = url; // SET SOURCE.
                        document.body.appendChild(objFra); // APPEND THE FRAME TO THE PAGE.
                        objFra.contentWindow.focus(); // SET FOCUS.
                        objFra.contentWindow.print();
                        return true;
                    }
                });    
            }
            else{
                if (this.override_session) {
                            options.data.session_id = this.session_id;
                        }
                        options.session = this;
                        return ajax.get_file(options);
                
            }    
        },
    });

    // Sidebar
    Sidebar.include({

        _redraw: function() {
            var self = this;
            this._super.apply(this, arguments);
            self.$el.find("a[href]").attr('target', '_blank');
        },
    });

});