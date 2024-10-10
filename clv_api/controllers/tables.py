from typing import Union

from odoo.api import Environment
from .model_converter import ModelConverter
from .tables_locations import TableLocationsProcessor
from .tables_customers_vendors import TableCustomersVendorsProcessor
from .tables_series import TableSeriesProcessor
from .tables_stock import TableStockProcessor
from .tables_warehouses_lines import TableWarehousesLinesProcessor
from .tables_inventory import TableInventoryProcessor
from .tables_contacts import TableContactsProcessor


class TablesImpl:
    """
    Supports /tables endpoint of the Inventory API
    """
    _model_converter = ModelConverter()

    # particular table rows request processors depends on its names
    _table_processor = {
        'warehouseslines': TableWarehousesLinesProcessor(),
        'locations': TableLocationsProcessor(),
        'series': TableSeriesProcessor(),
        'stock': TableStockProcessor(),
        'customersvendors': TableCustomersVendorsProcessor(),
        'inventory': TableInventoryProcessor(),
        'contacts': TableContactsProcessor()
    }

    def get_rows(self, env: Environment, query, device_info, offset, limit, request_count: bool):
        """
        Returns the page of rows depends on passed query
        @param env: Environment
        @param query: Inventory API query object
        @param device_info: Inventory API DeviceInfo
        @param offset: first record index to return
        @param limit: the maximum number of records to return
        @param request_count: need to return total number of records in query
        @return:
        """
        
        key = query['from'].lower()
        if key in self._table_processor:
            return self._table_processor[key].get_rows(env, query, device_info, offset, limit, request_count)
        else:
            return {"result": []}
