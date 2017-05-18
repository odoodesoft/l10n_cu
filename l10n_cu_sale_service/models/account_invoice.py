# -*- coding: utf-8 -*-


from openerp import api, fields, models, _
from openerp.exceptions import except_orm, Warning, RedirectWarning



class AccountInvoice(models.Model):
    _name = "account.invoice"
    _inherit = ["account.invoice", "ir.needaction_mixin"]

    no_complete_tasks = fields.Boolean('Have no complete tasks', compute='_compute_no_complete_tasks')
    force_invoice_validation = fields.Boolean('Force invoice validation')

    @api.one
    # Marcando las facturas cuyas lineas estan asociadas a tareas que no esten al 100% de progreso.
    def _compute_no_complete_tasks(self):
        task_obj = self.env['project.task']
        sale_line_obj = self.env['sale.order.line']
        for invoice_line in self.invoice_line:
                    sale_line_ids = sale_line_obj.search([('invoice_lines', '=', invoice_line.id)])
                    if sale_line_ids:
                        task_ids = task_obj.search([('sale_line_id', '=', sale_line_ids.id)])
                        if task_ids and not task_ids.progress == 100:
                            self.no_complete_tasks = True

    @api.model
    def _needaction_domain_get(self):
        # Adicionando un domain q obtenga las facturas provenientes de
        # pedidos cuyas tareas asociadas no estan al 100% de progreso.
        _dom_ = super(AccountInvoice, self)._needaction_domain_get()
        invoices = self.env['project.task'].search([
                                            ('progress', '<', 100)
                                            ]).mapped(
                                                'sale_line_id.invoice_lines.invoice_id.id')
        domain = ['|',('id', 'in', invoices)]
        return domain + _dom_

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('search_default_message_unread', False):
            args += self._needaction_domain_get()
        return super(AccountInvoice, self)._search(
                    args, offset=offset, limit=limit, order=order,
                    count=count, access_rights_uid=access_rights_uid)

    @api.multi
    def invoice_validate(self):
        # Al validar la factura (vista formulario o listado), validar si el pedido del cual proviene esta
        # asociado a una tarea que no esté al 100% de progreso y mostrar un mensaje de advertencia indicando
        # el problema, si se decide validar de todas formas mostrar un mensaje en el log asi como contar las
        # facturas con esa condicion y mostrar la notificacion del numero en el menu correspondiente.
        task_obj = self.env['project.task']
        sale_line_obj = self.env['sale.order.line']
        sale_obj = self.env['sale.order']
        order_ids = sale_obj.search([('invoice_ids', 'in', self.id)])
        db = self._cr.dbname
        action = self.env.ref('project.action_view_task', False)
        for order_id in order_ids:
            tasks = {}
            if order_id.order_policy == 'manual':
                for invoice_line in self.invoice_line:
                    sale_line_ids = sale_line_obj.search([('invoice_lines', '=', invoice_line.id)])
                    if sale_line_ids:
                        task_ids = task_obj.search([('sale_line_id', '=', sale_line_ids.id)])
                        if task_ids:
                            #
                            if not task_ids.progress == 100 and not self._context.get('force_invoice_validation', False) and \
                                    not self.force_invoice_validation == True:
                                # msg1=""
                                raise except_orm(_('Warning!'),
                                                 _("Some of the invoices you are trying to validate are associated to a task(s) that is/are not at 100 of progress \n"))
                                # for t in task_ids:
                                #     msg1 += "- %s\n" % (t.name)
                                # msgf = msg + msg1
                                # raise except_orm(_('Warning!'),msgf)
                            tasks.setdefault(task_ids.id, {})
                            tasks[task_ids.id].update({'db': db,
                                              'action_id': action.id,
                                              'task_id': task_ids.id,
                                              'task_name': task_ids.name})
                            msg = _("The invoice you validated is associated to a task(s):<br>")
                            self.with_context(
                            default_starred=False, #mark message as to-do
                            mail_post_autofollow=True,
                            ).message_post(body=msg)
                            msg_id = self.user_id.with_context(
                            default_starred=False, #mark message as to-do
                            mail_post_autofollow=True,
                            ).message_post(body=msg)
                            if msg_id:
                                self.env['mail.message'].browse(msg_id).set_message_starred(True)
                            for t in tasks.values():
                                msg1 = _("Task"'<a href ="/web?db=%s#id=%s&view_type=form&model=project.task&action=%s"> %s </a>'"is not at 100 of progress<br>") % \
                                       (t['db'], t['task_id'], t['action_id'], t['task_name'])
                                self.with_context(
                                default_starred=False, #mark message as to-do
                                mail_post_autofollow=True,
                                ).message_post(body=msg1, parent_id=msg_id)
                                msg_id1 = self.user_id.with_context(
                                default_starred=False, #mark message as to-do
                                mail_post_autofollow=True,
                                ).message_post(body=msg1, parent_id=msg_id)
                                if msg_id1:
                                    self.env['mail.message'].browse(msg_id1).set_message_starred(True)
        return super(AccountInvoice, self).invoice_validate()

    @api.multi
    def invoice_validate_force(self):
        return self.with_context(force_invoice_validation=True).invoice_validate()

    # @api.multi
    # def invoice_validate(self, flag):
    #     # Al crear la factura, validar si el pedido del cual proviene esta asociado a una tarea que no esté
    #     # al 100% de progreso y mostrar un mensaje en el log asi como contar las facturas con esa condicion
    #     # y mostrar la notificacion del numero en el menu correspondiente.
    #     if flag:
    #         task_obj = self.env['project.task']
    #         sale_line_obj = self.env['sale.order.line']
    #         sale_obj = self.env['sale.order']
    #         order_id = sale_obj.search([('invoice_ids', 'in', self.id)])
    #         db = self._cr.dbname
    #         action = self.env.ref('project.action_view_task', False)
    #         tasks = {}
    #         if order_id.order_policy == 'manual':
    #             for invoice_line in self.invoice_line:
    #                 sale_line_ids = sale_line_obj.search([('invoice_lines', '=', invoice_line.id)])
    #                 if sale_line_ids:
    #                     task_ids = task_obj.search([('sale_line_id', '=', sale_line_ids.id)])
    #                     if task_ids.progress < 100:
    #                         tasks.setdefault(task_ids.id, {})
    #                         tasks[task_ids.id].update({'db': db,
    #                                       'action_id' : action.id,
    #                                       'task_id' :task_ids.id,
    #                                       'task_name':task_ids.name})
    #         msg = _("The invoice you validated is associated to a task(s):<br>")
    #         self.with_context(
    #         default_starred=False, #mark message as to-do
    #         mail_post_autofollow=True,
    #         ).message_post(body=msg)
    #         msg_id = self.user_id.with_context(
    #         default_starred=False, #mark message as to-do
    #         mail_post_autofollow=True,
    #         ).message_post(body=msg)
    #         if msg_id:
    #             self.env['mail.message'].browse(msg_id).set_message_starred(True)
    #         for t in tasks.values():
    #             msg1 = _("Task"'<a href ="/web?db=%s#id=%s&view_type=form&model=project.task&action=%s"> %s </a>'"is not at 100 of progress<br>") % \
    #                    (t['db'], t['task_id'], t['action_id'], t['task_name'])
    #             self.with_context(
    #             default_starred=False, #mark message as to-do
    #             mail_post_autofollow=True,
    #             ).message_post(body=msg1, parent_id=msg_id)
    #             msg_id1 = self.user_id.with_context(
    #             default_starred=False, #mark message as to-do
    #             mail_post_autofollow=True,
    #             ).message_post(body=msg1, parent_id=msg_id)
    #             if msg_id1:
    #                 self.env['mail.message'].browse(msg_id1).set_message_starred(True)
    #     return super(AccountInvoice, self).invoice_validate()
    #
    #
    #
