import unittest

from app.models import Daily
from app.models import Monthly


class TestDailyBalance(unittest.TestCase):
    def test_daily_balance_1(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        d = Daily(0, "", 0, 0)
        r = d.get_daily_balance(450) # 7h 30m

        # assert
        self.assertEqual(r, "-0h 30m")

    def test_daily_balance_2(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        d = Daily(0, "", 0, 0)
        r = d.get_daily_balance(490) # 8h 10m

        # assert
        self.assertEqual(r, "0h 10m")

    def test_daily_balance_3(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        d = Daily(0, "", 0, 0)
        r = d.get_daily_balance(410) # 6h 50m

        # assert
        self.assertEqual(r, "-1h 10m")
    
    def test_daily_balance_4(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        d = Daily(0, "", 0, 0)
        r = d.get_daily_balance(550) # 9h 10m

        # assert
        self.assertEqual(r, "1h 10m")


class TestMonthlyBalance(unittest.TestCase):
    def test_monthly_balance_1(self):
        """Make sure the status_code is mandatory"""
        # arrange and act
        d = Monthly(0, "", "", 0, 0, 0)
        r = d.get_monthly_balance(930, 2) # -30min over 2 days where 8h each day is expected

        # assert
        self.assertEqual(r, "-0h 30m")
