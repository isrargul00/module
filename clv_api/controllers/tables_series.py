import datetime
from typing import List

from odoo.release import version_info
from .field_info import FieldInfo
from .tables_base import TableProcessorBase
from odoo.api import Environment


class TableSeriesProcessor(TableProcessorBase):
    """
    Processes requests to Series (batches/lots) table.
    The structure of the TableSeriesRow object is:
    barcode:
        type: string
        description: ???
    code:
        type: string
        description: ???
    description:
        type: string
        description: ???
    id:
        type: string
        description: ???
    number:
        type: string
        description: ???
    search:
        type: string
        description: ???
    seriesDate:
        type: string ($datetime)
        description: ???
    seriesKey:
        type: string
        description: ???
    seriesName:
        type: string
        description: ???
    sortIndex:
        type: number ($int32)
        description: ???
    """

    _mapping_fields: List[FieldInfo] = [
        FieldInfo(api_name_arg='barcode', api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='code', api_type_arg=str, odoo_name_arg='ref', odoo_type_arg=str),
        FieldInfo(api_name_arg='description', api_type_arg=str, odoo_name_arg='note', odoo_type_arg=str),
        FieldInfo(api_name_arg='id', api_type_arg=str, odoo_name_arg='id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='number', api_type_arg=str, odoo_name_arg='number', odoo_type_arg=str),
        FieldInfo(api_name_arg='seriesDate'.lower(), api_type_arg=str, odoo_name_arg='create_date', odoo_type_arg=datetime.datetime),
        FieldInfo(api_name_arg='seriesName'.lower(), api_type_arg=str, odoo_name_arg='name', odoo_type_arg=str),
        FieldInfo(api_name_arg='seriesKey'.lower(), api_type_arg=str, odoo_name_arg='product_id', odoo_type_arg=int, odoo_null_value_equivalent_arg='-1'),
        FieldInfo(api_name_arg='sortIndex'.lower(), api_type_arg=int, odoo_name_arg='sort_index', odoo_type_arg=int)
    ]

    def __init__(self):
        self._api_to_odoo_map = FieldInfo.create_api_to_odoo_field_map(self._mapping_fields)

    def _get_rows_int(self, env: Environment, query, device_info, offset, limit, request_count: bool):
        where_root = query.get('whereTreeRoot')

        domain_filter = [('product_id.product_tmpl_id.tracking', '=', 'lot')]

        pick_doc = self.cutils.get_odoo_doc_from_device_info(env, device_info)
        self.cutils.append_company_filter_by_doc(domain_filter, pick_doc)

        if where_root:
            additional_filter = self._query_converter.convert_api_where_expression_to_domain_filter(where_root, self._api_to_odoo_map)
            additional_filter = self._modify_domain_query(env, additional_filter)
            domain_filter.extend(additional_filter)

        stock_lot_entity_name = self.cutils.get_stock_lot_env_name()
        if request_count:
            rows_count = env[stock_lot_entity_name].search_count(domain_filter)
            return [rows_count, None]

        series = env[stock_lot_entity_name].search(domain_filter, limit=limit, offset=offset, order='id ASC')
        rows = [self._model_converter.convert_odoo_lot_to_series(s) for s in series]
        return [None, rows]

    # noinspection PyMethodMayBeStatic
    def _modify_domain_query(self, env, domain_filter):
        result = []
        for origin_field_filter in domain_filter:
            modified_field_filter = origin_field_filter
            if isinstance(origin_field_filter, tuple):
                field_name = origin_field_filter[0]
                if field_name == 'note':
                    modified_field_filter = self._modify_note_field_filter(env, origin_field_filter)
                elif field_name == 'number':
                    modified_field_filter = self._modify_number_field_filter(env, origin_field_filter)
                elif field_name == 'ref':
                    modified_field_filter = self._modify_ref_field_filter(env, origin_field_filter)
                elif field_name == 'sort_index':
                    modified_field_filter = self._modify_sort_index_field_filter(env, origin_field_filter)

                result.append(modified_field_filter)

        return result

    # noinspection PyMethodMayBeStatic
    def _modify_ref_field_filter(self, env, origin_filter):
        if origin_filter[2] is None or origin_filter[2] == '':
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], False)
        return origin_filter

    # noinspection PyMethodMayBeStatic
    def _modify_note_field_filter(self, env, origin_filter):
        if origin_filter[2] is None or origin_filter[2] == '':
            # noinspection PyRedundantParentheses
            return (origin_filter[0], origin_filter[1], False)
        return origin_filter

    # noinspection PyMethodMayBeStatic
    def _modify_number_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)

    # noinspection PyMethodMayBeStatic
    def _modify_sort_index_field_filter(self, env, origin_filter):
        # noinspection PyRedundantParentheses
        return ('id', '=' if not ((origin_filter[1] == '=') ^ bool(origin_filter[2])) else '!=', False)
