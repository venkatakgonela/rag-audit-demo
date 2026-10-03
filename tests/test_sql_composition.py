import ast
import re
from pathlib import Path

import pytest
from psycopg import sql

from rag_audit import retrieval
from rag_audit.access import ACL_SQL

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", ("__main__", "regression", "reranker_trial"))
@pytest.mark.parametrize(
    "schema", ("synthetic_schema", 'synthetic"; DROP SCHEMA public;--')
)
def test_schema_lifecycle_uses_identifiers_at_each_call_site(module, schema):
    source = (ROOT / f"src/rag_audit/evaluation/{module}.py").read_text()
    tree = ast.parse(source)
    expressions = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
            and node.args
        ):
            continue
        expression = node.args[0]
        segment = ast.get_source_segment(source, expression)
        if segment and "schema" in segment:
            assert "sql.Identifier(schema)" in segment
            assert not any(
                isinstance(child, ast.JoinedStr) for child in ast.walk(expression)
            )
            assert isinstance(expression, ast.Call)
            assert isinstance(expression.func, ast.Attribute)
            assert expression.func.attr == "format"
            template_call = expression.func.value
            assert isinstance(template_call, ast.Call)
            assert ast.unparse(template_call.func) == "sql.SQL"
            assert len(template_call.args) == 1 and not template_call.keywords
            assert len(expression.args) == 1 and not expression.keywords
            assert ast.unparse(expression.args[0]) == "sql.Identifier(schema)"
            template = ast.literal_eval(template_call.args[0])
            composed = sql.SQL(template).format(sql.Identifier(schema))
            assert isinstance(composed, sql.Composed)
            expressions.append(composed.as_string())
    quoted = '"' + schema.replace('"', '""') + '"'
    assert sorted(expressions) == sorted(
        (
            f"CREATE SCHEMA {quoted}",
            f"SET search_path TO {quoted},public",
            f"DROP SCHEMA {quoted} CASCADE",
        )
    )


def test_retrieval_queries_have_only_expected_bound_placeholders():
    expected = {
        "model",
        "tiers",
        "teams",
        "subject",
        "role",
        "vector",
        "query",
        "candidates",
        "top_k",
    }
    for statement, names in (
        (retrieval.SQL, expected),
        (retrieval.DOCUMENT_SQL, expected | {"documents"}),
    ):
        assert set(re.findall(r"%\((\w+)\)s", statement)) == names
        assert "%" not in re.sub(r"%\(\w+\)s", "", statement)
        assert "{" not in statement and "}" not in statement
        assert ACL_SQL in statement
    assert retrieval.DOCUMENT_SQL == retrieval.SQL.replace(
        "WHERE c.model_identity=",
        "WHERE d.id = ANY(%(documents)s) AND c.model_identity=",
    )


def test_retrieval_execution_selects_constants_and_binds_values():
    tree = ast.parse((ROOT / "src/rag_audit/retrieval.py").read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    assignments = [
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "query_sql"
            for target in node.targets
        )
    ]
    assert all(isinstance(value, ast.Name) for value in assignments)
    assert {ast.unparse(value) for value in assignments} == {"SQL", "DOCUMENT_SQL"}
    executions = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "query_sql"
    ]
    assert len(executions) == 1
    assert [ast.unparse(argument) for argument in executions[0].args] == [
        "query_sql",
        "parameters",
    ]
