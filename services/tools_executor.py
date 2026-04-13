from services.search_service import search_orders

async def execute_tool(tool, args):
    if tool == "search_orders":
        return search_orders(
            args["first_name"],
            args["last_name"]
        )

    return []