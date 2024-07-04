from lambda_functions.get_account_ids import app


def test_create_timeframes():

    assert app.create_timeframes("2024-07-04") == {
        "timeframes": {
            "new_data": {"start_date": "2024-04-01", "end_date": "2024-04-01"},
            "backfill": {"start_date": "2021-03-01", "end_date": "2024-03-01"},
        }
    }
