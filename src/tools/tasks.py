"""Task management tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from ..auth0 import Auth0Mcp
from ..auth0.authz import require_scopes
from ..espocrm import WhereClause
from .base import apply_fga, format_entity_list, format_json, get_espocrm_client


def register_task_tools(mcp: Auth0Mcp.mcp_class) -> None:

    @mcp.tool(
        name="create_task",
        title="Create Task",
        description="Create a new task and assign it to a user with optional parent entity",
    )
    @require_scopes(["espocrm:tasks:write"])
    async def create_task(
        name: str,
        assigned_user_id: str | None = None,
        parent_type: str | None = None,
        parent_id: str | None = None,
        status: str = "Not Started",
        priority: str = "Normal",
        date_end: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {"name": name, "status": status, "priority": priority}
        if assigned_user_id:
            data["assignedUserId"] = assigned_user_id
        if parent_type:
            data["parentType"] = parent_type
        if parent_id:
            data["parentId"] = parent_id
        if date_end:
            data["dateEnd"] = date_end
        if description:
            data["description"] = description

        result = await client.post("Task", data)
        task_id = result.get("id")
        extra_info = ""
        if assigned_user_id:
            extra_info += f" assigned to user {assigned_user_id}"
        if parent_type:
            extra_info += f" linked to {parent_type} {parent_id}"
        return f"Successfully created task: {name} (ID: {task_id}){extra_info}"

    @mcp.tool(
        name="search_tasks",
        title="Search Tasks",
        description="Search for tasks using flexible criteria",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:tasks:read"])
    async def search_tasks(
        name: str | None = None,
        assigned_user_id: str | None = None,
        assigned_user_name: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        parent_type: str | None = None,
        parent_id: str | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        limit: int = 20,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        where = []
        if name:
            where.append(WhereClause(type="contains", attribute="name", value=name))
        if assigned_user_id:
            where.append(
                WhereClause(
                    type="equals", attribute="assignedUserId", value=assigned_user_id
                )
            )
        if assigned_user_name:
            where.append(
                WhereClause(
                    type="contains",
                    attribute="assignedUserName",
                    value=assigned_user_name,
                )
            )
        if status:
            where.append(WhereClause(type="equals", attribute="status", value=status))
        if priority:
            where.append(
                WhereClause(type="equals", attribute="priority", value=priority)
            )
        if parent_type:
            where.append(
                WhereClause(type="equals", attribute="parentType", value=parent_type)
            )
        if parent_id:
            where.append(
                WhereClause(type="equals", attribute="parentId", value=parent_id)
            )
        if due_date_from:
            where.append(
                WhereClause(
                    type="greaterThanOrEquals", attribute="dateEnd", value=due_date_from
                )
            )
        if due_date_to:
            where.append(
                WhereClause(
                    type="lessThanOrEquals", attribute="dateEnd", value=due_date_to
                )
            )

        response = await client.search(
            "Task",
            where=where if where else None,
            select=[
                "id",
                "name",
                "status",
                "priority",
                "assignedUserName",
                "parentType",
                "parentName",
                "dateEnd",
            ],
            max_size=limit,
            offset=offset,
            order_by="dateEnd",
        )

        return format_entity_list(response.list or [], "tasks")

    @mcp.tool(
        name="get_task",
        title="Get Task",
        description="Get detailed information about a specific task",
        annotations={"readOnlyHint": True},
    )
    @require_scopes(["espocrm:tasks:read"])
    @apply_fga("get_task")
    async def get_task(task_id: str, ctx: Context | None = None) -> str:
        client = get_espocrm_client()
        task = await client.get_by_id("Task", task_id)
        return format_json(task)

    @mcp.tool(
        name="update_task", title="Update Task", description="Update an existing task"
    )
    @require_scopes(["espocrm:tasks:write"])
    @apply_fga("update_task")
    async def update_task(
        task_id: str,
        name: str | None = None,
        assigned_user_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        date_end: str | None = None,
        description: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()

        data = {}
        if name is not None:
            data["name"] = name
        if assigned_user_id is not None:
            data["assignedUserId"] = assigned_user_id
        if status is not None:
            data["status"] = status
        if priority is not None:
            data["priority"] = priority
        if date_end is not None:
            data["dateEnd"] = date_end
        if description is not None:
            data["description"] = description

        await client.put("Task", task_id, data)
        return f"Successfully updated task with ID: {task_id}"

    @mcp.tool(
        name="assign_task",
        title="Assign Task",
        description="Assign or reassign a task to a specific user",
    )
    @require_scopes(["espocrm:tasks:write"])
    @apply_fga("assign_task")
    async def assign_task(
        task_id: str,
        assigned_user_id: str,
        ctx: Context | None = None,
    ) -> str:
        client = get_espocrm_client()
        await client.put("Task", task_id, {"assignedUserId": assigned_user_id})
        return f"Successfully assigned task {task_id} to user {assigned_user_id}"
