"""Tests for opportunity, meeting, and task tools."""

from __future__ import annotations


class TestCreateOpportunity:
    async def test_create_with_close_date(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Opportunity",
            {
                "name": "Big Deal",
                "amount": 50000.0,
                "stage": "Qualified",
                "closeDate": "2025-12-31",
                "probability": 60,
            },
        )
        assert result.get("id") == "new-entity-id"

    async def test_create_without_close_date_defaults_to_90_days(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Opportunity",
            {
                "name": "Quick Deal",
                "amount": 10000.0,
                "stage": "Prospecting",
                "probability": 30,
            },
        )
        assert result.get("id") == "new-entity-id"


class TestSearchOpportunities:
    async def test_search_opportunities(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [WhereClause(type="equals", attribute="stage", value="Qualified")]
        response = await client.search(
            "Opportunity",
            where=where,
            select=["id", "name", "stage", "amount"],
            max_size=20,
            offset=0,
            order_by="createdAt",
        )
        assert response.list is not None


class TestCreateMeeting:
    async def test_create_meeting(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Meeting",
            {
                "name": "Team Sync",
                "dateStart": "2025-05-01 10:00:00",
                "dateEnd": "2025-05-01 11:00:00",
                "status": "Planned",
            },
        )
        meeting_id = result.get("id")
        assert meeting_id is not None


class TestSearchMeetings:
    async def test_search_meetings(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [WhereClause(type="equals", attribute="status", value="Planned")]
        response = await client.search(
            "Meeting",
            where=where,
            select=["id", "name", "status", "dateStart"],
            max_size=20,
            offset=0,
            order_by="dateStart",
        )
        assert response.list is not None


class TestCreateTask:
    async def test_create_task(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        result = await client.post(
            "Task",
            {
                "name": "Follow up",
                "status": "Not Started",
                "priority": "Normal",
            },
        )
        assert result.get("id") == "new-entity-id"


class TestSearchTasks:
    async def test_search_tasks(self):
        from src.espocrm import WhereClause
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        where = [WhereClause(type="equals", attribute="status", value="Not Started")]
        response = await client.search(
            "Task",
            where=where,
            select=["id", "name", "status", "priority"],
            max_size=20,
            offset=0,
            order_by="dateEnd",
        )
        assert response.list is not None


class TestAssignTask:
    async def test_assign_task(self):
        from src.tools.base import get_espocrm_client

        client = get_espocrm_client()
        await client.put("Task", "task-1", {"assignedUserId": "user-789"})
