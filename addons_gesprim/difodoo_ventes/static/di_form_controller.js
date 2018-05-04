odoo.define('web.DiFormController', function (require) {
"use strict";

var FormController = require('web.FormController');
var dialogs = require('web.view_dialogs');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Sidebar = require('web.Sidebar');

var _t = core._t;
var qweb = core.qweb;

var DiFormController = FormController.include({
    
    read_prop : function (obj, prop) {
        return obj[prop];
    },
    /**
     * @private
     */
    _updateButtons: function () {
            
        
        if (this.$buttons) {
            if (this.footerToButtons) {
                var $footer = this.$('footer');
                if ($footer.length) {
                    this.$buttons.empty().append($footer);
                }
            }
            var edit_mode = (this.mode === 'edit');
            var record = this.model.get(this.handle).data;
            var invoice_status = record.invoice_status;
//             this.$buttons.find('.o_form_buttons_edit')
//                          .toggleClass('o_hidden', !edit_mode);
//                          
//             this.$buttons.find('.o_form_buttons_view')
//                      .toggleClass('o_hidden', edit_mode);
                     
            if (this.modelName == 'sale.order' && invoice_status == 'invoiced'){
            
                //var $di_buttons = $('<button/>');
                 
                //$di_buttons.append(qweb.render("FormView.buttons", {widget: this}));
                //window.alert('true');
                
//                 $di_buttons.find('o_form_button_edit')
//                          .toggleClass('o_hidden', true);
                         
                this.$buttons.find('.o_form_buttons_edit')
                         .toggleClass('o_hidden', !edit_mode); 
                                   
                this.$buttons.find('.o_form_buttons_view')
                         .toggleClass('o_hidden', true); 
                         
              
              
                //window.alert(invoice_status);
                //window.alert(Object.entries(record));
                //window.alert(Object.values(record));
                //window.alert(record.fieldsInfo);         
               } 
            else{
                //window.alert('false');  
                this.$buttons.find('.o_form_buttons_edit')
                         .toggleClass('o_hidden', !edit_mode);
                         
                this.$buttons.find('.o_form_buttons_view')
                         .toggleClass('o_hidden', edit_mode);  
            }                                
            
//             if (this.modelName == 'sale.order'){
//                 if (edit_mode === true){ 
//                 
// //                     window.alert('true');
// //                     this.model.get(this.handle).getContext().append(['di_edit',true]);
//                 }
//             }
    //        var record = this.model.get(this.handle);        
  //          var context= record.getContext();
//            window.alert(this.model);
            //window.alert(record.toString);
            
        }
        
    },
  
});

return DiFormController;

});
