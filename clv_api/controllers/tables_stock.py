from typing import List

from .common_utils import CommonUtils
from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from odoo.api import Environment


class TableStockProcessor(TableProcessorBase):
    """
    Processes requests to Stock table.
    The structure of TableStockRow object is:
    attributeId:
        type: string
        description: Identifier of the inventory item's attribute.
    inventoryItemCode:
        type: string
        description: ???
    inventoryItemId:
        type: string
        description: ???
    locationId:
        type: string
        description: ???
    quantity:
        type: number
        description: ???
    quantityForPlacement:
        type: number
        description: ???
    quantityForTaking:
        type: number
        description: ???
    serialNumber:
        type: string
        description: Individual serial number of the inventory item. Typically, is unique.
    seriesId:
        type: string
        description: Identifier of the inventory item's series.
    transportUnitId:
        type: string
        description: ???
    unitId:
        type: string
        description:
            Unit of measure identifier without a postfix '_x'.
            For example, an inventory item may have three units of measure
            with identifiers 'pc_1', 'pc_2', 'pc_3' – for all of them this field will be equal to 'pc'.
    warehouseId:
        type: string
        description: ???
    """

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='attributeId'.lower(), api_type_arg=str, odoo_name_arg='attribute_id', odoo_type_arg=str),
        FieldInfo(api_name_arg='inventoryItemCode'.lower(), api_type_arg=str, odoo_name_arg='product_id.default_code', odoo_type_arg=str),
        FieldInfo(api_name_arg='inventoryItemId'.lower(), api_type_arg=str, odoo_name_arg='product_id.id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='locationId'.lower(), api_type_arg=str, odoo_name_arg='location_id.id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='quantity', api_type_arg=float, odoo_name_arg='available_quantity', odoo_type_arg=float),
        FieldInfo(api_name_arg='quantityForPlacement'.lower(), api_type_arg=float, odoo_name_arg='quantity_for_placement', odoo_type_arg=float),
        FieldInfo(api_name_arg='quantityForTaking'.lower(), api_type_arg=float, odoo_name_arg='reserved_quantity', odoo_type_arg=float),
        FieldInfo(api_name_arg='serialNumber'.lower(), api_type_arg=str, odoo_name_arg='lot_id.name', odoo_type_arg=str),
        FieldInfo(api_name_arg='seriesId'.lower(), api_type_arg=str, odoo_name_arg='lot_id.id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='transportUnitId'.lower(), api_type_arg=str, odoo_name_arg='transport_unit_id', odoo_type_arg=str),
        FieldInfo(api_name_arg='unitId'.lower(), api_type_arg=str, odoo_name_arg='product_uom_id.id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='warehouseId'.lower(), api_type_arg=str, odoo_name_arg='location_id.warehouse_id.id', odoo_type_arg=str, odoo_null_value_equivalent_arg='-1')
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool) -> List:
        where_root = query.get('whereTreeRoot')

        domain_filter = [
            ('location_id.active', '=', True)
        ]

        if where_root:
            additional_filter = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            additional_filter = self._modify_domain_query(env, additional_filter)
            domain_filter.extend(additional_filter)

        if request_count:
            rows_count = env['stock.quant'].search_count(domain_filter)
            return [rows_count, None]
        
        # Arrange stock quantities in descending order of the write date in order to get the most recent ones first
        stock_quants = env['stock.quant'].search(domain_filter, limit=limit, offset=offset, order='write_date DESC, id ASC')

        rows = []
        for stock_quant in stock_quants:
            rows.append(self._model_converter.convert_odoo_stock_quant_to_stock_row(stock_quant))

        return [None, rows]

    # noinspection PyMethodMayBeStatic
    def _modify_domain_query(self, env, domain_filter):
        result = []
        for origin_field_filter in domain_filter:
            modified_field_filter = origin_field_filter
            if isinstance(origin_field_filter, tuple):
                field_name = origin_field_filter[0]
                if field_name == 'attribute_id':
                    modified_field_filter = self._modify_attribute_id_field_filter(env, origin_field_filter)
                elif field_name == 'available_quantity':
                    modified_field_filter = self._modify_available_quantity_field_filter(env, origin_field_filter)
                elif field_name == 'quantity_for_placement':
                    modified_field_filter = self._modify_quantity_for_placement_field_filter(env, origin_field_filter)
                elif field_name == 'transport_unit_id':
                    modified_field_filter = self._modify_transport_unit_id_field_filter(env, origin_field_filter)
                elif field_name == 'location_id.warehouse_id.id':
                    modified_field_filter = self._modify_warehouse_id_field_filter(env, origin_field_filter)

            result.append(modified_field_filter)

        return result

    # noinspection PyMethodMayBeStatic
    def _modify_attribute_id_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_available_quantity_field_filter(self, env, origin_filter):
        # 'available_quantity' is calculated and non-stored field of 'stock.quant'
        # therefore it is not impossible to use it in domain filter directly.
        # To solve this, we use this tricky way with additional request to 'stock.quant' table.
        # Direct SQL-request is using to improve performance.
        operator = origin_filter[1]
        value = origin_filter[2]

        query = f"""
                    SELECT sq.id
                    FROM stock_quant sq
                    JOIN stock_location sl ON sq.location_id = sl.id
                    WHERE (sq.quantity - sq.reserved_quantity) {operator} {value}
                    AND sl.active = True
                """
        env.cr.execute(query)
        stock_quants = env.cr.fetchall()
        ids = [stock_quant[0] for stock_quant in stock_quants]

        # noinspection PyRedundantParentheses
        return ('id', 'in', ids)

    # noinspection PyMethodMayBeStatic
    def _modify_quantity_for_placement_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_transport_unit_id_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_warehouse_id_field_filter(self, env, origin_filter):
        if isinstance(origin_filter[2], str) and origin_filter[2].startswith('clv_wh_'):
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], CommonUtils.convert_warehouse_id_from_clv_to_odoo(origin_filter[2]))
        return origin_filter
