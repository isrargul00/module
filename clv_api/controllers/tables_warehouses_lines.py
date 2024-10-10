import logging
from typing import List
from odoo.api import Environment

from .clv_settings_provider import ClvSettingsProvider
from .common_utils import CommonUtils
from .field_info import FieldInfo
from .tables_base import TableProcessorBase


class TableWarehousesLinesProcessor(TableProcessorBase):
    """
    Processes requests to WarehousesLines table.
    The structure of the TableWarehousesLinesRow object is:
    addressable:
        type: boolean
    barcode:
        type: string
    code:
        type: string
    id:
        type: string
    isFolder:
        type: boolean
    name:
        type: string
    parentId:
        type: string
    search:
        type: string
        description: "Concatenated data in a lower case for searching."
    """

    _logger = logging.getLogger(__name__)

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=str, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='name', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='code', api_type_arg=str, odoo_name_arg='code', odoo_type_arg=str),
        # fake for conversion
        FieldInfo(api_name_arg='barcode', api_type_arg=str, odoo_name_arg='barcode', odoo_type_arg=str),
        FieldInfo(api_name_arg='addressable', api_type_arg=bool, odoo_name_arg='addressable', odoo_type_arg=bool),
        FieldInfo(api_name_arg='isfolder', api_type_arg=bool, odoo_name_arg='is_folder', odoo_type_arg=bool),
        FieldInfo(api_name_arg='parentid', api_type_arg=str, odoo_name_arg='parent_id', odoo_type_arg=str),
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool):
        where_root = query.get('whereTreeRoot')
        result = [None, []]
        domain_filter = [
            ('active', '=', True),
            ('company_id.active', '=', True)
        ]

        # If 'deviceInfo' contains information about document
        # then if possible we try to add a filter by company
        # in order to return only warehouses of the company that is selected in the document.
        found_doc = self.cutils.get_odoo_doc_from_device_info(env, device_info)
        self.cutils.append_company_filter_by_doc(domain_filter, found_doc)

        if where_root:
            domain_query_list = self._query_converter \
                .convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            domain_query_list = self._modify_domain_query(env, domain_query_list)
            domain_filter.extend(domain_query_list)

        if request_count:
            result[0] = env['stock.warehouse'].search_count(domain_filter)

        warehouses = env['stock.warehouse'].search(domain_filter, limit=limit, offset=offset, order='id ASC')
        locations_enabled = CommonUtils.is_storage_locations_enabled(env) and ClvSettingsProvider(env).default_scan_locations

        rows = []
        for warehouse in warehouses:
            row = {
                'id': CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id),
                'name': self._model_converter.clear_to_str(warehouse.name),
                'code': self._model_converter.clear_to_str(warehouse.code),
                'barcode': '',
                'parentId': '',
                'isFolder': False,
                'addressable': locations_enabled and bool(warehouse.lot_stock_id.child_ids),
                'search': CommonUtils.generate_search_string([warehouse.name, warehouse.code])
            }
            rows.append(row)

        result[1] = rows
        return result

    # noinspection PyMethodMayBeStatic
    def _modify_domain_query(self, env, domain_filter):
        result = []
        for origin_field_filter in domain_filter:
            modified_field_filter = origin_field_filter
            if isinstance(origin_field_filter, tuple):
                field_name = origin_field_filter[0]
                if field_name == 'id':
                    modified_field_filter = self._modify_id_field_filter(env, origin_field_filter)
                elif field_name == 'barcode':
                    modified_field_filter = self._modify_barcode_field_filter(env, origin_field_filter)
                elif field_name == 'addressable':
                    modified_field_filter = self._modify_addressable_field_filter(env, origin_field_filter)
                elif field_name == 'is_folder':
                    modified_field_filter = self._modify_is_folder_field_filter(env, origin_field_filter)
                elif field_name == 'parent_id':
                    modified_field_filter = self._modify_parent_id_field_filter(env, origin_field_filter)

            result.append(modified_field_filter)

        return result

    # noinspection PyMethodMayBeStatic
    def _modify_id_field_filter(self, env, origin_filter):
        if isinstance(origin_filter[2], str) and origin_filter[2].startswith('clv_wh_'):
            # noinspection PyRedundantParentheses
            return ('id', origin_filter[1], CommonUtils.convert_warehouse_id_from_clv_to_odoo(origin_filter[2]))
        return origin_filter

    # noinspection PyMethodMayBeStatic
    def _modify_addressable_field_filter(self, env, origin_filter):
        locations_enabled = CommonUtils.is_storage_locations_enabled(env) and ClvSettingsProvider(env).default_scan_locations

        # A tricky way to process filtering by 'addressable' field
        # but in the future it is better to extend the 'stock.warehouse' table
        if locations_enabled:
            # noinspection PyRedundantParentheses
            return ('lot_stock_id.child_ids', '=' if (origin_filter[1] == '=') ^ origin_filter[2] else '!=', False)
        else:
            # noinspection PyRedundantParentheses
            return ('id', '=' if not ((origin_filter[1] == '=') ^ origin_filter[2]) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_barcode_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_is_folder_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ origin_filter[2]) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_parent_id_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)
