"""Pruebas sintéticas del limitador persistente de solicitudes."""
from concurrent.futures import ProcessPoolExecutor
import sqlite3
import tempfile
from pathlib import Path
import unittest

from scripts.market_selection.shared_request_rate_limiter import (
    RateLimitCoordinationError,
    wait_for_rate_slot,
)


def _reserve_in_process(arguments):
    database, _index = arguments
    wait_for_rate_slot(
        "synthetic_source",
        20,
        database,
        sleep=lambda _delay: None,
        clock=lambda: 500.0,
    )
    return True


class SharedRequestRateLimiterTests(unittest.TestCase):
    def test_reservations_are_persisted_between_invocations(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "rate.sqlite3"
            waits = []
            clock = lambda: 100.0

            wait_for_rate_slot("synthetic_source", 10, database, sleep=waits.append, clock=clock)
            wait_for_rate_slot("synthetic_source", 10, database, sleep=waits.append, clock=clock)

            with sqlite3.connect(database) as connection:
                next_allowed = connection.execute(
                    "SELECT next_allowed_epoch FROM request_slots WHERE source_id = ?",
                    ("synthetic_source",),
                ).fetchone()[0]

            self.assertAlmostEqual(next_allowed, 100.2)
            self.assertEqual(len(waits), 1)
            self.assertAlmostEqual(waits[0], 0.1)

    def test_concurrent_reservations_share_one_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "rate.sqlite3"
            count = 12

            with ProcessPoolExecutor(max_workers=count) as executor:
                results = list(executor.map(_reserve_in_process, [(str(database), index) for index in range(count)]))
            self.assertEqual(results, [True] * count)

            with sqlite3.connect(database) as connection:
                next_allowed = connection.execute(
                    "SELECT next_allowed_epoch FROM request_slots WHERE source_id = ?",
                    ("synthetic_source",),
                ).fetchone()[0]

            self.assertAlmostEqual(next_allowed, 500.0 + count / 20)

    def test_coordination_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            invalid_database_path = Path(directory)
            with self.assertRaisesRegex(RateLimitCoordinationError, "network request blocked"):
                wait_for_rate_slot(
                    "synthetic_source",
                    1,
                    invalid_database_path,
                    sleep=lambda _delay: None,
                    clock=lambda: 1.0,
                )

    def test_invalid_rate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for rate in (0, -1):
                with self.subTest(rate=rate):
                    with self.assertRaisesRegex(RateLimitCoordinationError, "positive number"):
                        wait_for_rate_slot(
                            "synthetic_source",
                            rate,
                            Path(directory) / f"rate-{rate}.sqlite3",
                            sleep=lambda _delay: None,
                            clock=lambda: 1.0,
                        )

    def test_non_finite_rates_are_rejected_before_ledger_access(self):
        with tempfile.TemporaryDirectory() as directory:
            for rate in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(rate=str(rate)):
                    database = Path(directory) / f"rate-{len(list(Path(directory).iterdir()))}.sqlite3"
                    with self.assertRaisesRegex(RateLimitCoordinationError, "finite positive number"):
                        wait_for_rate_slot(
                            "synthetic_source",
                            rate,
                            database,
                            sleep=lambda _delay: None,
                            clock=lambda: 1.0,
                        )
                    self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
