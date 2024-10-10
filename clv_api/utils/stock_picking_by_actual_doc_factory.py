from typing import List

from odoo.api import Environment

from ..controllers.common_utils import CommonUtils


class StockPickingByActualDocFactory:

    @classmethod
    def create(cls, env: Environment, clv_doc: dict) -> object:
        """
        Creates a new 'stock.picking' in Odoo based on Cleverence document created on the mobile device.
        """

        # Correct field is 'warehouseId', 'warehouseExternalId' is left for backward compatibility
        warehouse_id = clv_doc.get('warehouseId', '') or clv_doc.get('warehouseExternalId', '')
        if not warehouse_id:
            raise RuntimeError('Warehouse is not specified')

        partner_id = clv_doc.get('customerVendorId', '')
        if not partner_id:
            raise RuntimeError('Partner is not specified')

        warehouse_id = CommonUtils.convert_warehouse_id_from_clv_to_odoo(warehouse_id)
        warehouse = env['stock.warehouse'].search([('id', '=', warehouse_id), ('active', '=', True)], limit=1)

        if not warehouse:
            raise RuntimeError('Unknown or inactive warehouse')

        partner = env['res.partner'].search([('id', '=', partner_id), ('active', '=', True)], limit=1)
        if not partner:
            raise RuntimeError('Unknown or inactive partner')

        operation_code = False
        doc_type_name = clv_doc.get('documentTypeName', '').lower()
        if doc_type_name == 'receiving':
            if warehouse.reception_steps != 'one_step':
                raise RuntimeError('Creating documents on the mobile device is supported only for one-step receiving process')
            operation_code = 'incoming'
        elif doc_type_name == 'ship':
            if warehouse.delivery_steps != 'ship_only':
                raise RuntimeError('Creating documents on the mobile device is supported only for one-step shipping process')
            operation_code = 'outgoing'
        else:
            raise RuntimeError(
                f'Creating documents on the mobile device is not supported for \'{doc_type_name}\' document type')

        picking_types = env['stock.picking.type'].search([
            ('active', '=', True),
            ('warehouse_id', '=', warehouse_id),
            ('code', '=', operation_code)])

        if not picking_types:
            raise RuntimeError('Operation type for this document not found')

        # Temporally we select the first one,
        # but actually we need to select between several picking types.
        picking_type = picking_types[0]

        stock_picking = env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'partner_id': partner.id,
            'origin': cls._generate_origin_for_stock_picking(clv_doc),
            'company_id': warehouse.company_id.id
        })

        actual_lines = clv_doc.get('actualLines', [])
        grouped_actual_quantities = cls._group_actual_quantities(actual_lines)

        for group_key, quantity in grouped_actual_quantities.items():
            stock_picking.move_ids_without_package.create({
                'picking_id': stock_picking.id,
                'product_id': group_key[0],
                'product_uom': group_key[1],
                'product_uom_qty': quantity,
                'picked': False,
                'location_id': stock_picking.location_id.id,
                'location_dest_id': stock_picking.location_dest_id.id,
                'name': cls._generate_stock_move_name(clv_doc),
                'company_id': stock_picking.company_id.id
            })

        stock_picking.action_assign()

        return stock_picking

    @classmethod
    def _group_actual_quantities(cls, actual_lines: List) -> dict:
        result = {}
        for actual_line in actual_lines:
            product_id = int(actual_line.get('inventoryItemId'))
            uom_id = int(actual_line.get('unitOfMeasureId'))
            actual_qty = actual_line.get('actualQuantity')

            key = (product_id, uom_id)
            if key in result:
                result[key] += actual_qty
            else:
                result[key] = actual_qty

        return result

    @classmethod
    def _generate_origin_for_stock_picking(cls, clv_doc: dict) -> str:
        doc_name = clv_doc.get('name', 'UNKNOWN_DOC').upper()
        user_id = clv_doc.get('userId', 'UNKNOWN_USER').upper()
        device_id = clv_doc.get('deviceId', 'UNKNOWN_DEVICE').upper()

        return f'{doc_name} by {user_id} with {device_id}'

    @classmethod
    def _generate_stock_move_name(cls, clv_doc: dict) -> str:
        user_id = clv_doc.get('userId', 'UNKNOWN_USER').upper()
        device_id = clv_doc.get('deviceId', 'UNKNOWN_DEVICE').upper()

        return f'Stock move by {user_id} with {device_id}'
