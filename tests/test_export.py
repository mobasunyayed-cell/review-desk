import csv
import io

import pytest

from conftest import sign_in
from review_desk.export import safe_cell
from test_reviews import RUBRIC, TASK, review


@pytest.fixture
def filled(client):
    task = client.post("/tasks", json=TASK).json()
    rubric = client.post("/rubrics", json=RUBRIC).json()
    ids = [c["id"] for c in rubric["criteria"]]
    client.post(
        f"/tasks/{task['id']}/reviews",
        json=review(rubric["id"], ids, [5, 5], comment='=HYPERLINK("http://evil")'),
    )
    client.headers.update(sign_in(client, "dr-b"))
    client.post(f"/tasks/{task['id']}/reviews", json=review(rubric["id"], ids, [2, 10]))
    return client, rubric["id"]


def test_json_export_has_one_row_per_review(filled):
    client, rubric_id = filled
    rows = client.get(f"/rubrics/{rubric_id}/export").json()
    assert [r["reviewer"] for r in rows] == ["dr-a", "dr-b"]
    assert rows[0]["Accuracy"] == 5 and rows[0]["Safety"] == 5
    assert rows[0]["total"] == pytest.approx(0.875)
    assert rows[1]["total"] == pytest.approx((3 * 0.4 + 1.0) / 4)


def test_csv_export_parses_and_neutralises_formulas(filled):
    client, rubric_id = filled
    response = client.get(f"/rubrics/{rubric_id}/export", params={"format": "csv"})
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert list(rows[0])[-3:] == ["Safety", "total", "comment"]
    assert rows[0]["comment"].startswith("'=")  # not a live formula
    assert rows[1]["comment"] == ""


def test_empty_rubric_exports_header_only(client):
    rubric = client.post("/rubrics", json=RUBRIC).json()
    assert client.get(f"/rubrics/{rubric['id']}/export").json() == []
    text = client.get(f"/rubrics/{rubric['id']}/export?format=csv").text
    assert text.strip().split("\n") == [
        "review_id,task_id,task_title,reviewer,created_at,Accuracy,Safety,total,comment"
    ]


def test_export_errors_and_auth(client, anonymous):
    assert client.get("/rubrics/99/export").status_code == 404
    assert client.get("/rubrics/1/export?format=xml").status_code == 422
    assert anonymous.get("/rubrics/1/export").status_code in (401, 403)


@pytest.mark.parametrize("value", ["=1+1", "+1", "-1", "@x", "\tx"])
def test_safe_cell_prefixes_dangerous_values(value):
    assert safe_cell(value) == "'" + value


def test_safe_cell_leaves_normal_values_alone():
    assert safe_cell("Aspirin") == "Aspirin" and safe_cell(3) == 3 and safe_cell(None) is None
