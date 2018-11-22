from odoo import api, models, _


rec = 0
def autoIncrement():
    global rec
    pStart = 1
    pInterval = 1
    if rec == 0:
        rec = pStart
    else:
        rec += pInterval
    return rec



class MrpStockReport(models.TransientModel):
    _inherit = "stock.traceability.report"
    
    @api.model
    def _final_vals_to_lines(self, final_vals, level):
        lines = []
        for data in final_vals:
            lines.append({
                'id': autoIncrement(),
                'model': data['model'],
                'model_id': data['model_id'],
                'parent_id': data['parent_id'],
                'usage': data.get('usage', False),
                'is_used': data.get('is_used', False),
                'lot_name': data.get('lot_name', False),
                'lot_id': data.get('lot_id', False),
                'reference': data.get('reference_id', False),
                'res_id': data.get('res_id', False),
                'res_model': data.get('res_model', False),
                'columns': [data.get('reference_id', False),
                            data.get('product_id', False),
                            data.get('date', False),
                            data.get('lot_name', False),
                            data.get('location_source', False),
                            data.get('location_destination', False),
                            data.get('partner',False),
                            data.get('product_qty_uom', 0)],
                'level': level,
                'unfoldable': data['unfoldable'],
            })
        return lines
    
    
    
    def _make_dict_move(self, level, parent_id, move_line, unfoldable=False):
        res_model, res_id, ref = self._get_reference(move_line)
        dummy, is_used = self._get_linked_move_lines(move_line)
        data = [{
            'level': level,
            'unfoldable': unfoldable,
            'date': move_line.move_id.date,
            'parent_id': parent_id,
            'is_used': bool(is_used),
            'usage': self._get_usage(move_line),
            'model_id': move_line.id,
            'model': 'stock.move.line',
            'product_id': move_line.product_id.display_name,
            'product_qty_uom': "%s %s" % (self._quantity_to_str(move_line.product_uom_id, move_line.product_id.uom_id, move_line.qty_done), move_line.product_id.uom_id.name),
            'lot_name': move_line.lot_id.name,
            'lot_id': move_line.lot_id.id,
            'location_source': move_line.location_id.name,
            'location_destination': move_line.location_dest_id.name,
            'partner': move_line.move_id.partner_id.name or False,
            'reference_id': ref,
            'res_id': res_id,
            'res_model': res_model}]
        return data
    
     

#     def make_dict_head(self, level, parent_id, model=False, stream=False, move_line=False):
#         data = []
#         if model == 'stock.move.line':
#             data = [{
#                 'level': level,
#                 'unfoldable': True,
#                 'date': move_line.move_id.date,
#                 'model_id': move_line.id,
#                 'parent_id': parent_id,
#                 'model': model or 'stock.move.line',
#                 'product_id': move_line.product_id.display_name,
#                 'lot_id': move_line.lot_id.name,
#                 'product_qty_uom': "%s %s" % (self._quantity_to_str(move_line.product_uom_id, move_line.product_id.uom_id, move_line.qty_done), move_line.product_id.uom_id.name),
#                 'location': move_line.location_dest_id.name,
#                 'partner': move_line.move_id.partner_id.name or False,
#                 'stream': stream,
#                 'reference_id': False}]
#         elif model == 'stock.quant':
#             data = [{
#                 'level': level,
#                 'unfoldable': True,
#                 'date': move_line.write_date,
#                 'model_id': move_line.id,
#                 'parent_id': parent_id,
#                 'model': model or 'stock.quant',
#                 'product_id': move_line.product_id.display_name,
#                 'lot_id': move_line.lot_id.name,
#                 'product_qty_uom': "%s %s" % (self._quantity_to_str(move_line.product_uom_id, move_line.product_id.uom_id, move_line.quantity), move_line.product_id.uom_id.name),
#                 'location': move_line.location_id.name,
#                 'partner': False,
#                 'stream': stream,
#                 'reference_id': False}]
#         return data  
    
#     def get_pdf_lines(self, line_data=[]):
#         final_vals = []
#         lines = []
#         for line in line_data:
#             model = self.env[line['model_name']].browse(line['model_id'])
#             if line.get('unfoldable'):
#                     final_vals += self.make_dict_head(line['level'], model=line['model_name'], parent_id=line['id'], move_line=model)
#             else:
#                 if line['model_name'] == 'stock.move.line':
#                     final_vals += self.make_dict_move(line['level'], parent_id=line['id'], move_line=model)
#         for data in final_vals:
#             lines.append({
#                 'id': autoIncrement(),
#                 'model': data['model'],
#                 'model_id': data['model_id'],
#                 'parent_id': data['parent_id'],
#                 'stream': "%s" % (data['stream']),
#                 'type': 'line',
#                 'name': _(data.get('lot_id')),
#                 'columns': [data.get('reference_id') or data.get('product_id'),
#                             data.get('lot_id'),
#                             data.get('date'),
#                             data.get('product_qty_uom', 0),
#                             data.get('location'),
#                             data.get('partner')],
#                 'level': data['level'],
#                 'unfoldable': data['unfoldable'],
#             })
# 
#         return lines
#     
    