# from odoo import models, api, _
# from odoo.exceptions import UserError
#
#
# class PosSession(models.Model):
#     _inherit = 'pos.session'
#
#     def _get_difference_account(self):
#         # Get the config parameter value (it's the account.account record id stored as string)
#         param = self.env['ir.config_parameter'].sudo()
#         account_id_str = param.get_param('pos_dinger.default_pos_receivable_difference_account_id')
#         if account_id_str:
#             account = self.env['account.account'].browse(int(account_id_str))
#             if account.exists():
#                 return account
#         return False
#
#     def _create_bank_payment_moves(self, data):
#         data = super()._create_bank_payment_moves(data)
#
#
#         difference_account = self._get_difference_account()
#
#         # Fixed difference amount
#         difference_amount = 20.0
#
#         # That part is right
#         # Add a new journal line for the difference amount
#         difference_account_id = difference_account.id
#
#         if not difference_account_id:
#             raise UserError(_('Please configure an account for cash difference in the company settings.'))
#
#             # Find one bank payment line in the move (usually crediting the receivable)
#             payment_line = self.move_id.line_ids.filtered(
#                 lambda line: line.account_id.user_type_id.type == 'receivable' and line.credit > 0
#             )
#             if not payment_line:
#                 raise UserError(_('Could not find a payment line to adjust in the accounting move.'))
#
#             line_to_adjust = payment_line[0]  # Pick first matching line
#
#             # Reduce credit (i.e., what customer paid)
#             new_credit = line_to_adjust.credit - difference_amount
#             if new_credit < 0:
#                 raise UserError(_('Difference amount exceeds the original payment line.'))
#
#             # line_to_adjust.write({
#             #     'credit': new_credit
#             # })
#
#         self.env['account.move.line'].create({
#             'name': _('Cash Difference'),
#             'move_id': self.move_id.id,
#             'account_id': difference_account_id,
#             'debit': difference_amount if difference_amount > 0 else 0.0,
#             'credit': 0.0,
#             'partner_id': False,
#             # other fields as needed (analytic account, currency, etc.)
#         })
#
#         return data
from odoo import models, api, _
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _get_difference_account(self):
        param = self.env['ir.config_parameter'].sudo()
        account_id_str = param.get_param('pos_dinger.default_pos_receivable_difference_account_id')
        if account_id_str:
            account = self.env['account.account'].browse(int(account_id_str))
            if account.exists():
                return account
        return False

    def _create_bank_payment_moves(self, data):
        data = super()._create_bank_payment_moves(data)

        difference_amount = 20.0
        difference_account = self._get_difference_account()
        if not difference_account:
            raise UserError(_('Please configure an account for POS difference in settings.'))

        # 🔎 Find a receivable line (usually the customer's payment line)
        payment_line = self.move_id.line_ids.filtered(
            lambda line: line.credit > 0
        )
        if not payment_line:
            raise UserError(_('Could not find a receivable line to adjust.'))

        receivable_line = payment_line[0]

        if receivable_line.credit < difference_amount:
            raise UserError(_('Difference amount exceeds the receivable amount.'))

        # ✏️ Reduce the credit amount of the original line
        receivable_line.write({
            'credit': receivable_line.credit - difference_amount,
        })

        # ➕ Add a debit line for the difference
        self.env['account.move.line'].create({
            'name': _('Cash Difference'),
            'move_id': self.move_id.id,
            'account_id': difference_account.id,
            'debit': difference_amount,
            'credit': 0.0,
            'partner_id': receivable_line.partner_id.id,
        })

        # ➕ Add an opposite credit line to keep journal balanced
        self.env['account.move.line'].create({
            'name': _('Difference at closing PoS session'),
            'move_id': self.move_id.id,
            'account_id': difference_account.id,
            'debit': 0.0,
            'credit': difference_amount,
            'partner_id': receivable_line.partner_id.id,
        })

        return data

