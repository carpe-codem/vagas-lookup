#!/usr/bin/env python2
import unittest
import vl
import pandas as pd


class TestLines(unittest.TestCase):
    def test(self):
        network_type = 'walk'
        address = 'R. John Kennedy, 180 - Barra da Tijuca, Rio de Janeiro - RJ, 22620-260, Brazil'
        df = pd.read_csv("vagas.csv")
        lines = vl.get_waypoints_by_address(address, vagas_df=df, maxtime=15)
        self.assertEqual(lines[10], [(-43.3197797, -23.0104479), (-43.3208006, -23.0101969)])

if __name__ == '__main__':
    unittest.main()
