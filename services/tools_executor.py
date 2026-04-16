from services.search_service import search_orders_multi


async def execute_tool(tool_name, args):
    if tool_name == "search_orders_multi":
        return await search_orders_multi(**args)

    return None