from typing import List

from .clv_settings_provider import ClvSettingsProvider
from .common_utils import CommonUtils
from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from odoo.api import Environment


class TableLocationsProcessor(TableProcessorBase):
    """
    Process location table requests.
    The structure of the TableLocationRow object is:
    id:
        type: string
        description: id of the location
    name:
        type: string
        description: name of the location
    barcode:
        type: string
        description: barcode of the location
    isGroup:
        type: boolean
        description: defines if the location has child locations
    notSelectable:
        type: boolean
        description: defines if the location can be selected on the mobile device
    parentId:
        type: string
        description: id of the parent location
    description:
        type: string
        description: description of the location
    """

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=str),
        FieldInfo(api_name_arg='name', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='barcode', api_type_arg=str, odoo_name_arg='barcode', odoo_type_arg=str)
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool):
        where_root = query.get('whereTreeRoot')

        pick_doc = self.cutils.get_odoo_doc_from_device_info(env, device_info)

        business_query = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
        business_query = self._remove_unsupported_filters(business_query)

        self.cutils.append_company_filter_by_doc(business_query, pick_doc)

        location_parent_path = self.cutils.get_location_parent_path_from_document(pick_doc)
        if location_parent_path:
            business_query.append(('parent_path', '=like', location_parent_path + '%'))

        if request_count:
            return [self._get_clv_locations_count(env, business_query), None]

        return [None, self._get_clv_locations(env, business_query, limit, offset)]

    def _get_clv_locations_count(self, env: Environment, additional_filter) -> int:
        warehouses_domain_filter = [
            ('active', '=', True),
            ('company_id.active', '=', True)
        ]

        warehouses_domain_filter.extend(self._prepare_filter_for_odoo_warehouses(additional_filter))
        warehouses_count = env['stock.warehouse'].search_count(warehouses_domain_filter)

        locations_domain_filter = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
            '|',
            ('company_id', '=', False),
            ('company_id.active', '=', True),
            '|',
            ('warehouse_id', '=', False),
            ('warehouse_id.active', '=', True)
        ]
        locations_domain_filter.extend(self._prepare_filter_for_odoo_locations(additional_filter))
        locations_count = env['stock.location'].search_count(locations_domain_filter)

        return warehouses_count + locations_count

    def _get_clv_locations(self, env: Environment, additional_filter, limit, offset):
        result = []

        warehouses_domain_filter = [
            ('active', '=', True),
            ('company_id.active', '=', True)
        ]
        warehouses_domain_filter.extend(self._prepare_filter_for_odoo_warehouses(additional_filter))
        warehouses = env['stock.warehouse'].search(warehouses_domain_filter, limit=limit, offset=offset, order='id ASC')

        for warehouse in warehouses:
            result.append({
                'id': CommonUtils.convert_warehouse_id_from_odoo_to_clv(warehouse.id),
                'name': self._model_converter.clear_to_str(warehouse.name),
                'barcode': '',
                'isGroup': bool(warehouse.lot_stock_id.id),
                'notSelectable': True,
                'parentId': self._model_converter.clear_to_str(warehouse.view_location_id.location_id.id)
            })

        locations_domain_filter = [
            '|',
            ('active', '=', True),
            ('active', '=', False),
            '|',
            ('company_id', '=', False),
            ('company_id.active', '=', True),
            '|',
            ('warehouse_id', '=', False),
            ('warehouse_id.active', '=', True)
        ]
        locations_domain_filter.extend(self._prepare_filter_for_odoo_locations(additional_filter))
        locations = env['stock.location'].search(locations_domain_filter, limit=limit, offset=offset, order='id ASC')

        for location in locations:
            parent_id = None
            if location.location_id:
                parent_id = location.location_id.id

            if location.usage == 'view':
                if location.warehouse_id:
                    if location.warehouse_id in warehouses:
                        parent_id = CommonUtils.convert_warehouse_id_from_odoo_to_clv(location.warehouse_id.id)

            barcode = location.complete_name
            if location.barcode:
                barcode = location.barcode

            not_selectable = not location.active \
                or location.usage in ['view'] \
                or (ClvSettingsProvider(env).allow_only_lowest_level_locations and len(location.child_ids) > 0)

            result.append({
                'id': self._model_converter.clear_to_str(location.id),
                'name': self._model_converter.clear_to_str(location.complete_name),
                'barcode': self._model_converter.clear_to_str(barcode),
                'isGroup': len(location.child_ids) > 0,
                'notSelectable': not_selectable,
                'parentId': self._model_converter.clear_to_str(parent_id)
            })

        return result

    def _prepare_filter_for_odoo_warehouses(self, domain_filter):
        result = []
        for item in domain_filter:
            filter_item = item
            if isinstance(item, tuple):
                if item[0].lower() == 'id' and isinstance(item[2], str):
                    if item[2].lower().startswith('clv_wh_'):
                        filter_item = (item[0], item[1], CommonUtils.convert_warehouse_id_from_clv_to_odoo(item[2]))
                    else:
                        return [('id', '=', False)]

                if item[0].lower() == 'barcode' or item[0].lower() == 'parent_path':
                    filter_item = ('id', '!=', False)

            result.append(filter_item)

        return result

    def _prepare_filter_for_odoo_locations(self, domain_filter):
        result = []
        for item in domain_filter:
            filter_item = item
            if isinstance(item, tuple):
                if item[0].lower() == 'id' and isinstance(item[2], str):
                    if item[2].lower().startswith('clv_wh_'):
                        return [('id', '=', False)]
                    else:
                        filter_item = (item[0], item[1], int(item[2]))

                if item[0].lower() == 'barcode':
                    result.extend(['|', filter_item, ('complete_name', '=', filter_item[2])])
                    continue

            result.append(filter_item)

        return result

    def _remove_unsupported_filters(self, domain_filter):
        result = []
        allowed_fields_for_filtering = ['id', 'name', 'barcode']
        for item in domain_filter:
            filter_item = item
            if isinstance(item, tuple) and not item[0] in allowed_fields_for_filtering:
                filter_item = ('id', '!=', False)

            result.append(filter_item)

        return result
