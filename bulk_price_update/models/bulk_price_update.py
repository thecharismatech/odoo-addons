from odoo import models, fields, api
from odoo.exceptions import UserError

class BulkPriceUpdate(models.Model):
    _name = 'bulk.price.update'
    _description = 'Bulk Price Update'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    fixed_amount = fields.Float(string='Fixed Amount', tracking=True)
    percentage = fields.Float(string='Percentage', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', default='draft', tracking=True)
    source_type = fields.Selection([
        ('purchase', 'Purchase Order'),
        ('stock', 'Stock Operation')
    ], string='Source Type', default='purchase', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', tracking=True)
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Operation', tracking=True)
    purchase_line_ids = fields.One2many(related='purchase_order_id.order_line', string='Purchase Lines')
    stock_move_ids = fields.One2many(related='stock_picking_id.move_ids', string='Stock Moves')
    notes = fields.Text('Notes')
    updated_line_ids = fields.One2many('bulk.price.update.line', 'bulk_update_id', string='Updated Products')

    @api.onchange('source_type', 'purchase_order_id', 'stock_picking_id', 'fixed_amount', 'percentage')
    def _onchange_update_lines(self):
        self.updated_line_ids = [(5, 0, 0)]
        values = []
        
        if self.source_type == 'purchase' and self.purchase_order_id:
            lines = self.purchase_line_ids
        elif self.source_type == 'stock' and self.stock_picking_id:
            lines = self.stock_move_ids
        else:
            return

        for line in lines:
            product = line.product_id
            old_price = product.list_price
            if self.fixed_amount:
                new_price = old_price + self.fixed_amount
            elif self.percentage:
                new_price = old_price * (1 + self.percentage / 100)
            else:
                new_price = old_price
            
            values.append((0, 0, {
                'product_id': product.id,
                'old_price': old_price,
                'new_price': new_price,
            }))
        self.updated_line_ids = values
    def bulk_update_prices(self):
        self.ensure_one()
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(self.env._("Only Purchase Managers can update prices"))
            
        if not self.fixed_amount and not self.percentage:
            raise UserError(self.env._("Please specify either Fixed Amount or Percentage"))
        
        if not self.purchase_order_id:
            raise UserError(self.env._("Please select a purchase order"))
        
        updated_count = 0
        for line in self.updated_line_ids:
            line.product_id.list_price = line.new_price
            updated_count += 1
        
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': self.env._('Successfully updated %s product sales prices', updated_count),
                'type': 'success',
                'sticky': False,
            }
        }

class BulkPriceUpdateLine(models.Model):
    _name = 'bulk.price.update.line'
    _description = 'Bulk Price Update Line'

    bulk_update_id = fields.Many2one('bulk.price.update', string='Bulk Update')
    product_id = fields.Many2one('product.product', string='Product')
    old_price = fields.Float(string='Old Price')
    new_price = fields.Float(string='New Price')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line')