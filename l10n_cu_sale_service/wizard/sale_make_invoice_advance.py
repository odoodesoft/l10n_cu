##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models, fields, _

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _compute_selection(self):
        res = super(SaleAdvancePaymentInv, self)._compute_selection()
        orders = self.env["sale.order"].browse(self._context.get('active_ids'))
        for o in orders:
            if o.order_policy == 'picking':
                products = o.order_line.filtered(
                                lambda l: l.product_id and l.product_id.type == 'service'
                                ).mapped('product_id')
                products._fields['auto_create_task'].group_operator = 'count'
                statistic = products.read_group(
                                [('id', 'in', products.ids)],
                                ['auto_create_task'],
                                ['auto_create_task'],
                                lazy=False)
                if len(statistic) >= 2 and len(res) > 1:
                    return res[3:]
        return res

    @api.multi
    def create_invoices(self):
        # Cuando el pedido contenga servicios que generan tareas, servicios que no generan tareas
        # y no contenga productos, solo se permitira utilizar el metodo de facturacion por lineas y
        # se excluiran las lineas que generan tarea pues esas se facturan desde el proyecto.
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        if self.advance_payment_method == 'lines':
            res['domain'] = ['|', ('order_id.order_policy', '=', 'manual'),
                             '&',('order_id.order_policy', '=', 'picking'),
                                  ('product_id.auto_create_task', '=', False)]
            # order_line = self.env["sale.order"].browse(
            #                     self._context.get('active_id'))
            # if order_line.order_policy == 'picking':
            #     lines = order_line.mapped('order_line').filtered(
            #                             lambda l: not l.product_id.auto_create_task
            #                             ).mapped('id')
            #
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
