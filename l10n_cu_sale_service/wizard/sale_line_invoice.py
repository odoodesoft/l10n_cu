# -*- coding: utf-8 -*-
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

from openerp import models, fields, api, _
from openerp.exceptions import (
        except_orm,
        Warning,
        RedirectWarning,
        ValidationError,
        )

class sale_order_line_make_invoice(models.TransientModel):
    _inherit = "sale.order.line.make.invoice"

    @api.multi
    def make_invoices(self):
        # para cuando el metodo de facturacion es Bajo demanda/Algunas lineas
        sale_order_line = self.env['sale.order.line'].browse(self._context.get('active_ids', []))
        inv_before = sale_order_line.filtered(lambda l: not l.invoiced and l.state not in ('draft', 'cancel')).mapped('order_id').mapped('invoice_ids')
        for line in sale_order_line:
            if not line.order_id.partner_id.property_account_receivable.id:
                raise ValidationError(_("The client do not has defined: The account!"))
        res = super(sale_order_line_make_invoice, self).make_invoices()

        # invalidate creation of invoice when all service that dont generate task are invoiced
        orders = sale_order_line.mapped('order_id').filtered(lambda o: o.order_policy == 'picking')
        if orders and not orders.mapped('order_line').filtered(
                                                    lambda l: not l.product_id.auto_create_task and
                                                          not l.invoiced).exists():
            orders.write({'state': 'progress'})

        inv_after = self.env['sale.order.line'].browse(self._context.get('active_ids', [])).mapped('order_id.invoice_ids')
        (inv_after - inv_before).write({'generate_by_other': True})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
