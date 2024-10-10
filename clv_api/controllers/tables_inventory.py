from typing import List

from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from odoo.api import Environment


class TableInventoryProcessor(TableProcessorBase):
    """
    Processes 'select' requests to inventory.
    Allows working with inventory as a table.
    Used exclusively for specific cases.
    """
    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='name', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='stockquantity', api_type_arg=float, odoo_name_arg='qty_available', odoo_type_arg=float),
        FieldInfo(api_name_arg='withserialnumber', api_type_arg=bool, odoo_name_arg='withserialnumber', odoo_type_arg=bool),
        FieldInfo(api_name_arg='withseries', api_type_arg=bool, odoo_name_arg='withseries', odoo_type_arg=bool)
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool) -> List:
        where_root = query.get('whereTreeRoot')

        domain_filter = [
            ('active', '=', True),
            ('detailed_type', '=', 'product')
        ]

        if where_root:
            additional_filter = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            additional_filter = self._replace_specific_filters(additional_filter)
            domain_filter.extend(additional_filter)

        result = [None, None]

        if request_count:
            result[0] = len(env['product.product'].search(domain_filter, limit=limit, offset=offset, order='id ASC'))

        items = env['product.product'].search(domain_filter, limit=limit, offset=offset, order='id ASC')

        rows = []
        for item in items:
            row = {
                'id': str(item.id),
                'name': str(item.name),
                'stockquantity': item.qty_available,
                'withserialnumber': item.tracking == 'serial',
                'withseries': item.tracking == 'lot'
            }
            rows.append(row)

        result[1] = rows

        return result

    @staticmethod
    def _convert_with_series_filter(value: tuple) -> tuple:
        if value[2]:
            return 'tracking', value[1], 'lot'

        inverted_comparison = '!=' if value[1] == '=' else '='
        return 'tracking', inverted_comparison, 'lot'

    @staticmethod
    def _convert_with_serial_number_filter(value: tuple) -> tuple:
        if value[2]:
            return 'tracking', value[1], 'serial'

        inverted_comparison = '!=' if value[1] == '=' else '='
        return 'tracking', inverted_comparison, 'serial'

    def _replace_specific_filters(self, domain_filter):
        result = []
        for item in domain_filter:
            filter_element = item
            if isinstance(filter_element, tuple):
                if filter_element[0].lower() == 'withseries':
                    filter_element = self._convert_with_series_filter(filter_element)
                elif filter_element[0].lower() == 'withserialnumber':
                    filter_element = self._convert_with_serial_number_filter(filter_element)

            result.append(filter_element)

        return result
