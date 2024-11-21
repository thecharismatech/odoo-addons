from odoo import models, fields, api

class BulkPriceUpdateLine(models.Model):
    _name = 'bulk.price.update.line'
    _description = 'Bulk Price Update Line'

    bulk_update_id = fields.Many2one('bulk.price.update', string='Bulk Update')
    product_id = fields.Many2one('product.product', string='Product')
    old_price = fields.Float(string='Old Price')
    new_price = fields.Float(string='New Price')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line')
    computed_new_price = fields.Float(string='Computed New Price', compute='_compute_new_price')

    @api.depends('bulk_update_id.fixed_amount', 'bulk_update_id.percentage', 'purchase_line_id.price_unit')
    def _compute_new_price(self):
        for line in self:
            current_price = line.purchase_line_id.price_unit
            if line.bulk_update_id.fixed_amount:
                line.computed_new_price = current_price + line.bulk_update_id.fixed_amount
            elif line.bulk_update_id.percentage:
                line.computed_new_price = current_price * (1 + line.bulk_update_id.percentage / 100)
            else:
                line.computed_new_price = current_price