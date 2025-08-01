# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, models
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        analytic_move_to_recompute = set()
        move_lines = super(StockMoveLine, self).create(vals_list)
        for move_line in move_lines:
            move = move_line.move_id
            analytic_move_to_recompute.add(move.id)
            move_line._update_svl_quantity(move_line.quantity)
        if analytic_move_to_recompute:
            self.env['stock.move'].browse(
                analytic_move_to_recompute)._account_analytic_entry_move()
        return move_lines

    def write(self, vals):
        analytic_move_to_recompute = set()
        if 'quantity' in vals or 'move_id' in vals:
            for move_line in self:
                move_id = vals.get('move_id', move_line.move_id.id)
                analytic_move_to_recompute.add(move_id)
        new_lot = False
        if 'lot_id' in vals:
            new_lot = vals.get('lot_id')
        if 'quant_id' in vals:
            new_quant = vals.get('quant_id')
            new_lot = self.env['stock.quant'].browse(new_quant).lot_id.id
        if new_lot:
            # remove quantity of old lot
            for move_line in self:
                move_line._update_svl_quantity(-move_line.quantity)
        elif 'quantity' in vals:
            # directly updates the right quantity if no lot change
            for move_line in self:
                move_line._update_svl_quantity(vals['quantity'] - move_line.quantity)
        if 'location_id' in vals or 'location_dest_id' in vals:
            for move_line in self:
                if move_line.state != 'done':
                    continue
                new_loc_id = vals.get('location_id', move_line.location_id.id)
                new_loc = self.env['stock.location'].browse(new_loc_id)
                new_dest_loc_id = vals.get('location_dest_id', move_line.location_dest_id.id)
                new_dest_loc = self.env['stock.location'].browse(new_dest_loc_id)
                if move_line.location_id._should_be_valued() != new_loc._should_be_valued() \
                        or move_line.location_dest_id._should_be_valued() != new_dest_loc._should_be_valued():
                    raise ValidationError(_("The stock valuation of a move is based on the type of the source and destination locations. "
                                            "As the move is already processed, you cannot modify the locations in a way that changes the "
                                            "valuation logic defined during the initial processing."))
        res = super().write(vals)
        if new_lot:
            # add quantity of new lot
            for move_line in self:
                move_line._update_svl_quantity(vals.get('quantity', move_line.quantity))
        if analytic_move_to_recompute:
            self.env['stock.move'].browse(analytic_move_to_recompute)._account_analytic_entry_move()
        return res

    def unlink(self):
        analytic_move_to_recompute = self.move_id
        res = super().unlink()
        analytic_move_to_recompute._account_analytic_entry_move()
        return res

    def _update_svl_quantity(self, added_qty):
        self.ensure_one()
        if self.state != 'done':
            return
        if self.product_id.lot_valuated and not self.lot_id:
            raise UserError(_('This product is valuated by lot: an explicit Lot/Serial number is required when adding quantity'))
        product_uom = self.product_id.uom_id
        added_uom_qty = self.product_uom_id._compute_quantity(added_qty, product_uom, rounding_method='HALF-UP')
        if float_is_zero(added_uom_qty, precision_rounding=product_uom.rounding):
            return
        self._create_correction_svl(self.move_id, added_uom_qty)

    def _action_done(self):
        for line in self:
            if not line.lot_id and not line.lot_name and line.product_id.lot_valuated:
                raise UserError(_("Lot/Serial number is mandatory for product valuated by lot"))
        return super()._action_done()

    # -------------------------------------------------------------------------
    # SVL creation helpers
    # -------------------------------------------------------------------------
    def _create_correction_svl(self, move, diff):
        lot = self.lot_id if self.product_id.lot_valuated else self.env['stock.lot']
        qty = (lot, abs(diff))
        stock_valuation_layers = self.env['stock.valuation.layer']
        if (move._is_in() and diff > 0) or (move._is_out() and diff < 0):
            move.product_price_update_before_done(forced_qty=(lot, diff))
            stock_valuation_layers |= move._create_in_svl(forced_quantity=qty)
            if move.product_id.cost_method in ('average', 'fifo'):
                move.product_id._run_fifo_vacuum(move.company_id)
        elif (move._is_in() and diff < 0) or (move._is_out() and diff > 0):
            stock_valuation_layers |= move._create_out_svl(forced_quantity=qty)
            if move.product_id.lot_valuated:
                move._product_price_update_after_done()
        elif (move._is_dropshipped() and diff > 0) or (move._is_dropshipped_returned() and diff < 0):
            stock_valuation_layers |= move._create_dropshipped_svl(forced_quantity=qty)
        elif (move._is_dropshipped() and diff < 0) or (move._is_dropshipped_returned() and diff > 0):
            stock_valuation_layers |= move._create_dropshipped_returned_svl(forced_quantity=qty)

        stock_valuation_layers._validate_accounting_entries()

    @api.model
    def _should_exclude_for_valuation(self):
        """
        Determines if this move line should be excluded from valuation based on its ownership.
        :return: True if the move line's owner is different from the company's partner (indicating
                it should be excluded from valuation), False otherwise.
        """
        self.ensure_one()
        return self.owner_id and self.owner_id != self.company_id.partner_id
