// odoo.define('di.impressionJS', function (require) {
// "use strict";
// 
// var di_form_widget = require('web.form_widgets');
// var core = require('web.core');
// var _t = core._t;
// var QWeb = core.qweb;
// 
// di_form_widget.WidgetButton.include({
//     on_click: function() {
//         window.alert('avant');
//          if(this.node.attrs.class === "di_imprimer_etiquette_JS"){
//             window.alert('dans');
//             var printWindow = window.open();
//             printWindow.document.open('text/plain');
//             printWindow.document.write('${}$');
//             printWindow.document.close();
//             printWindow.focus();
//             printWindow.print();
//             
// 
//             return;
//          }
//          this._super();
//     },
// });
// return di_form_widget;
// });
// // 
// // // import window;
// // //     function openWin(raw_data) {
// // //     var printWindow = window.open();
// // //     printWindow.document.open('text/plain');
// // //     printWindow.document.write('${'+raw_data+'}$');
// // //     printWindow.document.close();
// // //     printWindow.focus();
// // //     printWindow.print();
// // //   }
// // //   
// // // openWin("^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR6,6~SD15^JUS^LRN^CI0^XZ^XA^MMT^PW639^LL0799^LS0^BY2,3,160^FT566,701^BCB,,N,N^FD>;[codebarre[^FS^FT74,460^A0B,39,38^FB98,1,0,C^FH\^FD[codeart[^FS^FT128,703^A0B,28,28^FB583,2,1,C^FH\^FD[des[^FS^FT325,607^A0B,28,28^FH\^FDLot : ^FS^FT247,603^A0B,28,28^FH\^FDQuantit\82 : ^FS^FT324,541^A0B,28,28^FH\^FD[lot[^FS^FT247,476^A0B,28,28^FH\^FD[qte[^FS^FT583,570^A0B,16,16^FH\^FD[txtcb[^FS^PQ1,0,1,Y^XZ");
// // odoo.define('web.DiImpCli', function (require) {
// // "use strict";
// // 
// //     
// //     function openWin (raw_data) {
// //         var printWindow = window.open();
// //         printWindow.document.open('text/plain');
// //         printWindow.document.write('${'+raw_data+'}$');
// //         printWindow.document.close();
// //         printWindow.focus();
// //         printWindow.print();
// //     }
// // 
// // 
// // return openWin("^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR6,6~SD15^JUS^LRN^CI0^XZ^XA^MMT^PW639^LL0799^LS0^BY2,3,160^FT566,701^BCB,,N,N^FD>;[codebarre[^FS^FT74,460^A0B,39,38^FB98,1,0,C^FH\^FD[codeart[^FS^FT128,703^A0B,28,28^FB583,2,1,C^FH\^FD[des[^FS^FT325,607^A0B,28,28^FH\^FDLot : ^FS^FT247,603^A0B,28,28^FH\^FDQuantit\82 : ^FS^FT324,541^A0B,28,28^FH\^FD[lot[^FS^FT247,476^A0B,28,28^FH\^FD[qte[^FS^FT583,570^A0B,16,16^FH\^FD[txtcb[^FS^PQ1,0,1,Y^XZ");
// // 
// // });
