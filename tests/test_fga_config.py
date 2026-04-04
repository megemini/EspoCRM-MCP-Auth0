"""Tests for src/tools/fga_config.py."""

from __future__ import annotations

from src.tools.fga_config import (
    TOOL_FGA_RULES,
    FGARule,
    get_fga_rule,
    list_fga_protected_tools,
)


class TestFGARule:
    def test_default_relation(self):
        rule = FGARule(object_type="contact", object_id_param="contact_id")
        assert rule.relation == "can_read"

    def test_custom_relation(self):
        rule = FGARule(
            object_type="account",
            object_id_param="account_id",
            relation="can_update",
        )
        assert rule.relation == "can_update"


class TestToolFgaRules:
    def test_all_rules_use_valid_relations(self):
        valid_relations = {"can_read", "can_update", "can_delete", "can_assign"}
        for tool_name, rule in TOOL_FGA_RULES.items():
            assert (
                rule.relation in valid_relations
            ), f"{tool_name} uses invalid relation: {rule.relation}"

    def test_no_phantom_rules(self):
        actual_tool_names = {
            "get_contact",
            "get_meeting",
            "get_task",
            "get_entity",
            "update_account",
            "update_lead",
            "update_meeting",
            "update_task",
            "update_case",
            "update_entity",
            "delete_entity",
            "assign_lead",
            "assign_task",
            "convert_lead",
            "link_entities",
            "unlink_entities",
        }
        assert set(TOOL_FGA_RULES.keys()) == actual_tool_names

    def test_get_contact_rule(self):
        rule = get_fga_rule("get_contact")
        assert rule is not None
        assert rule.object_type == "contact"
        assert rule.object_id_param == "contact_id"
        assert rule.relation == "can_read"

    def test_update_account_rule(self):
        rule = get_fga_rule("update_account")
        assert rule is not None
        assert rule.object_type == "account"
        assert rule.relation == "can_update"

    def test_delete_entity_rule(self):
        rule = get_fga_rule("delete_entity")
        assert rule is not None
        assert rule.relation == "can_delete"

    def test_assign_task_rule(self):
        rule = get_fga_rule("assign_task")
        assert rule is not None
        assert rule.relation == "can_assign"

    def test_convert_lead_uses_can_update_not_can_write(self):
        rule = get_fga_rule("convert_lead")
        assert rule is not None
        assert (
            rule.relation == "can_update"
        ), "convert_lead should use can_update, not can_write"

    def test_link_entities_uses_can_update(self):
        rule = get_fga_rule("link_entities")
        assert rule is not None
        assert rule.relation == "can_update"

    def test_unlink_entities_uses_can_update(self):
        rule = get_fga_rule("unlink_entities")
        assert rule is not None
        assert rule.relation == "can_update"

    def test_generic_entity_rules_have_none_object_type(self):
        for tool_name in [
            "get_entity",
            "update_entity",
            "delete_entity",
            "link_entities",
            "unlink_entities",
        ]:
            rule = get_fga_rule(tool_name)
            assert rule is not None
            assert (
                rule.object_type is None
            ), f"{tool_name} should have dynamic object_type (None)"

    def test_unknown_tool_returns_none(self):
        assert get_fga_rule("nonexistent") is None


class TestListFgaProtectedTools:
    def test_returns_copy(self):
        result1 = list_fga_protected_tools()
        result2 = list_fga_protected_tools()
        assert result1 is not result2
        assert result1 == result2

    def test_count_matches_expected(self):
        rules = list_fga_protected_tools()
        assert len(rules) == 16
