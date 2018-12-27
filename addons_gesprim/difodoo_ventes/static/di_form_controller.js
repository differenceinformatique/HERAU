// odoo.define('web.DiFormController', function (require) {
// "use strict";
// 
// var FormController = require('web.FormController');
// var dialogs = require('web.view_dialogs');
// var core = require('web.core');
// var rpc = require('web.rpc');
// var Dialog = require('web.Dialog');
// var Sidebar = require('web.Sidebar');
// 
// var _t = core._t;
// var qweb = core.qweb;
// 
// var DiFormController = FormController.include({
// 
// 
// /**
//      * Show a warning message if the user modified a translated field.  For each
//      * field, the notification provides a link to edit the field's translations.
//      *
//      * @override
//      */
//     saveRecord: function () {
//         var self = this;
//         return this._super.apply(this, arguments).then(function (changedFields) {
//             // the title could have been changed
//             self.set('title', self.getTitle());
//             self._updateEnv();
// 
//             if (self.modelName == 'sale.order'){
//             
//                 self._rpc({model: 'sale.order', method: 'di_avec_lignes_a_zero', }).then(function (result){
//                     window.alert('di_avec_lignes_a_zero');
//                     if (result === true){
//                         window.alert('result true');
//                         if (window.confirm('Voulez-vous supprimer les lignes à 0 ?')) {
//                             window.alert('confirm');
//                             self._rpc({model: 'sale.order', method: 'di_supprimer_ligne_a_zero',});                            
//                             window.alert('suppr');
//                         } else {
//                             window.alert('rien');
//                             // Do nothing!
//                         }    
//                     }
//                 });                
//             }
//             
//             if (_t.database.multi_lang && changedFields.length) {
//                 // need to make sure changed fields that should be translated
//                 // are displayed with an alert
//                 var fields = self.renderer.state.fields;
//                 var data = self.renderer.state.data;
//                 var alertFields = [];
//                 for (var k = 0; k < changedFields.length; k++) {
//                     var field = fields[changedFields[k]];
//                     var fieldData = data[changedFields[k]];
//                     if (field.translate && fieldData) {
//                         alertFields.push(field);
//                     }
//                 }
//                 if (alertFields.length) {
//                     self.renderer.alertFields = alertFields;
//                     self.renderer.displayTranslationAlert();
//                 }
//             }
//             return changedFields;
//         });
//         }
//     
// //     read_prop : function (obj, prop) {
// //         return obj[prop];
// //     },
// //     
// //     di_openWin : function() {
// //         var printWindow = window.open();
// //         printWindow.document.open('text/plain');
// //         printWindow.document.write('${^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR6,6~SD15^JUS^LRN^CI0^XZ^XA^MMT^PW639^LL0799^LS0^BY2,3,160^FT566,701^BCB,,N,N^FD>;[codebarre[^FS^FT74,460^A0B,39,38^FB98,1,0,C^FH\^FD[codeart[^FS^FT128,703^A0B,28,28^FB583,2,1,C^FH\^FD[des[^FS^FT325,607^A0B,28,28^FH\^FDLot : ^FS^FT247,603^A0B,28,28^FH\^FDQuantit\82 : ^FS^FT324,541^A0B,28,28^FH\^FD[lot[^FS^FT247,476^A0B,28,28^FH\^FD[qte[^FS^FT583,570^A0B,16,16^FH\^FD[txtcb[^FS^PQ1,0,1,Y^XZ}$');
// //         printWindow.document.close();
// //         printWindow.focus();
// //         printWindow.print();
// //         printWindow.close();
// //     },
// //     /**
// //      * @private
// //      */
// //     _updateButtons: function () {
// //             
// //          
// //         if (this.$buttons) {
// //             if (this.footerToButtons) {
// //                 var $footer = this.$('footer');
// //                 if ($footer.length) {
// //                     this.$buttons.empty().append($footer);
// //                 }
// //             }
// //             var edit_mode = (this.mode === 'edit');
// //             var record = this.model.get(this.handle).data;
// //             var invoice_status = record.invoice_status;
// // //             var avec_lignes = false;
// // //             window.alert('avant');
// // //             window.alert(avec_lignes);
// // //             if  (this.modelName == 'sale.order'){
// // //                 var lignes = this.model.get(record.order_line.id).data;
// // // //                 var lignes = record.order_line.model.get(this.handle).data;
// // //                 window.alert(lignes);
// // //                 window.alert(lignes.id);
// // //                 window.alert(lignes.ids);
// // //                 
// // //                 avec_lignes = record.order_line.id;
// // // //                 window.alert('affect');
// // // //                 window.alert(avec_lignes);                    
// // //             }
// // //             else{
// // //                 avec_lignes = false;
// // // //                 window.alert('non_affect');
// // // //                 window.alert(avec_lignes);
// // //             }
// //             
// // //             this.$buttons.find('.o_form_buttons_edit')
// // //                          .toggleClass('o_hidden', !edit_mode);
// // //                          
// // //             this.$buttons.find('.o_form_buttons_view')
// // //                      .toggleClass('o_hidden', edit_mode);
// //                      
// //             if (this.modelName == 'sale.order' && invoice_status == 'invoiced'){// && avec_lignes !== false){
// // //                 window.alert('dans');
// // //                 window.alert(avec_lignes);
// //             
// //                 //var $di_buttons = $('<button/>');
// //                  
// //                 //$di_buttons.append(qweb.render("FormView.buttons", {widget: this}));
// //                 //window.alert('true');
// //                 
// // //                 $di_buttons.find('o_form_button_edit')
// // //                          .toggleClass('o_hidden', true);
// //                          
// //                 this.$buttons.find('.o_form_buttons_edit')
// //                          .toggleClass('o_hidden', !edit_mode); 
// //                                    
// //                 this.$buttons.find('.o_form_buttons_view')
// //                          .toggleClass('o_hidden', true); 
// //                          
// //               
// //               
// //                 //window.alert(invoice_status);
// //                 //window.alert(Object.entries(record));
// //                 //window.alert(Object.values(record));
// //                 //window.alert(record.fieldsInfo);         
// //                } 
// //             else{
// //                 //window.alert('false');  
// //                 this.$buttons.find('.o_form_buttons_edit')
// //                          .toggleClass('o_hidden', !edit_mode);
// //                          
// //                 this.$buttons.find('.o_form_buttons_view')
// //                          .toggleClass('o_hidden', edit_mode);  
// //             }                                
// //             
// // //             if (this.modelName == 'sale.order'){
// // //                 if (edit_mode === true){ 
// // //                 
// // // //                     window.alert('true');
// // // //                     this.model.get(this.handle).getContext().append(['di_edit',true]);
// // //                 }
// // //             }
// //     //        var record = this.model.get(this.handle);        
// //   //          var context= record.getContext();
// // //            window.alert(this.model);
// //             //window.alert(record.toString);
// //             
// //         }
// //         
// //     },
//   
// });
// 
// return DiFormController;
// 
// });
