odoo.define('web.DiFormController', function (require) {
"use strict";

var FormController = require('web.FormController');
var dialogs = require('web.view_dialogs');
var core = require('web.core');
var rpc = require('web.rpc');
var Dialog = require('web.Dialog');
var Sidebar = require('web.Sidebar');

var _t = core._t;
var qweb = core.qweb;

var DiFormController = FormController.include({
    //copie standard
    _onSave: function (ev) {
        ev.stopPropagation(); // Prevent x2m lines to be auto-saved
        var self = this;                
        this._disableButtons();
        this.saveRecord().always(function () {
            self._enableButtons();                     
            if (self.modelName == 'sale.order'){ // on vérifie qu'on est sur une commande ou devis de vente
            // à ce moment la commande est déjà sauvegardée ainsi que les lignes
                var env = self.model.get(self.handle, {env: true}); // récup de l'environnement              
                var id = env.currentId ? [env.currentId] : [];  // récup de l'id courant                                                 
                self._rpc({model: 'sale.order', method: 'di_avec_lignes_a_zero',  args: [id], }).then(function (result){
                //appel de la fonction di_avec_lignes_a_zero de la classe SaleOrder avec les arguments id                                                    
                    if (result === true){   // contrôle du retour de la fonction                    
                        if (window.confirm('Voulez-vous supprimer les lignes à 0 ?')) { // question
                            //appel de la fonction di_supprimer_ligne_a_zero de la classe SaleOrder avec les arguments id, suivi d'un appel à la fonction de rechargement de la page                           
                            self._rpc({model: 'sale.order', method: 'di_supprimer_ligne_a_zero', args: [id],}).then(function () {self.trigger_up('reload');});
                                                                                                                           
                        }  
                    }
                });   
                //appel de la fonction di_avec_lignes_mt_zero de la classe SaleOrder avec les arguments id 
                self._rpc({model: 'sale.order', method: 'di_avec_lignes_mt_zero',  args: [id], }).then(function (result){                                                    
                    if (result === true){                        
                        window.alert('Il y a des lignes avec montant à 0 !');                                                   
                    }
                });                
            }
            
        });        
    },
    
//     /**
//      * @private
//      */
//     _updateButtons: function () {
//             
//          
//         if (this.$buttons) {
//             if (this.footerToButtons) {
//                 var $footer = this.$('footer');
//                 if ($footer.length) {
//                     this.$buttons.empty().append($footer);
//                 }
//             }
//             var edit_mode = (this.mode === 'edit');
//             var record = this.model.get(this.handle).data;
//             var invoice_status = record.invoice_status;
// //             var avec_lignes = false;
// //             if  (this.modelName == 'sale.order'){
// //                 var lignes = this.model.get(record.order_line.id).data;
// // //                 var lignes = record.order_line.model.get(this.handle).data;                 
// //                 avec_lignes = record.order_line.id;             
// //             }
// //             else{
// //                 avec_lignes = false;
// //             }
//             
// //             this.$buttons.find('.o_form_buttons_edit')
// //                          .toggleClass('o_hidden', !edit_mode);
// //                          
// //             this.$buttons.find('.o_form_buttons_view')
// //                      .toggleClass('o_hidden', edit_mode);
//                      
//             if (this.modelName == 'sale.order' && invoice_status == 'invoiced'){// && avec_lignes !== false){
//             
//                 //var $di_buttons = $('<button/>');
//                  
//                 //$di_buttons.append(qweb.render("FormView.buttons", {widget: this}));
//                 
// //                 $di_buttons.find('o_form_button_edit')
// //                          .toggleClass('o_hidden', true);
//                          
//                 this.$buttons.find('.o_form_buttons_edit')
//                          .toggleClass('o_hidden', !edit_mode); 
//                                    
//                 this.$buttons.find('.o_form_buttons_view')
//                          .toggleClass('o_hidden', true);       
//                } 
//             else{
//                 this.$buttons.find('.o_form_buttons_edit')
//                          .toggleClass('o_hidden', !edit_mode);
//                          
//                 this.$buttons.find('.o_form_buttons_view')
//                          .toggleClass('o_hidden', edit_mode);  
//             }                                
//             
// //             if (this.modelName == 'sale.order'){
// //                 if (edit_mode === true){ 
// //                 
// // //                     this.model.get(this.handle).getContext().append(['di_edit',true]);
// //                 }
// //             }
//     //        var record = this.model.get(this.handle);        
//   //          var context= record.getContext();
//             
//         }
//         
//     },
  
});

return DiFormController;

});
