from services.search_service import search_orders


async def execute_tool(tool_name, args):
    if tool_name == "search_orders":
        return search_orders(
            args.get("first_name"),
            args.get("last_name")
        )

    return None