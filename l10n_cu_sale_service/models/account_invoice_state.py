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


from openerp import api, fields, models, _

class AccountInvoiceConfirm(models.TransientModel):
    """
    This wizard will confirm the selected draft invoices
    if the field for force invoice is selected when there are invoices
    that are associated to tasks that are not at 100% of progress .
    """

    _inherit = "account.invoice.confirm"

    wizard_force_validation = fields.Boolean('Force invoices validation')

    @api.multi
    def invoice_confirm(self):
        active_ids = self._context.get('active_ids', []) or []
        if self.wizard_force_validation == True:
            self.env['account.invoice'].browse(active_ids).filtered(
                        lambda s: s.state in ('draft', 'proforma', 'proforma2')).write({'force_invoice_validation': True})
        return super(AccountInvoiceConfirm, self).invoice_confirm()


