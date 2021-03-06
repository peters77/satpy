#!/usr/bin/env python
# Copyright (c) 2018 Satpy developers
#
# This file is part of satpy.
#
# satpy is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# satpy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# satpy.  If not, see <http://www.gnu.org/licenses/>.
"""Unittests for NWC SAF reader."""

import unittest

try:
    from unittest import mock
except ImportError:
    import mock

PROJ_KM = {'gdal_projection': '+proj=geos +a=6378.137000 +b=6356.752300 +lon_0=0.000000 +h=35785.863000',
           'gdal_xgeo_up_left': -5569500.0,
           'gdal_ygeo_up_left': 5437500.0,
           'gdal_xgeo_low_right': 5566500.0,
           'gdal_ygeo_low_right': 2653500.0}
PROJ = {'gdal_projection': '+proj=geos +a=6378137.000 +b=6356752.300 +lon_0=0.000000 +h=35785863.000',
        'gdal_xgeo_up_left': -5569500.0,
        'gdal_ygeo_up_left': 5437500.0,
        'gdal_xgeo_low_right': 5566500.0,
        'gdal_ygeo_low_right': 2653500.0}


class TestNcNWCSAF(unittest.TestCase):
    """Test the NcNWCSAF reader."""

    @mock.patch('satpy.readers.nwcsaf_nc.unzip_file')
    @mock.patch('satpy.readers.nwcsaf_nc.xr')
    def setUp(self, xr_, unzip):
        """Set up the test case."""
        from satpy.readers.nwcsaf_nc import NcNWCSAF
        xr_.return_value = mock.Mock(attrs={})
        unzip.return_value = ''
        self.scn = NcNWCSAF('filename', {}, {})

    def test_get_projection(self):
        """Test generation of the navigation info."""
        # a, b and h in kilometers
        self.scn.nc.attrs = PROJ_KM
        proj_str, area_extent = self.scn._get_projection()
        self.assertTrue('+units=km' in proj_str)
        self.assertAlmostEqual(area_extent[0],
                               PROJ_KM['gdal_xgeo_up_left'] / 1000.)
        self.assertAlmostEqual(area_extent[1],
                               PROJ_KM['gdal_ygeo_low_right'] / 1000.)
        self.assertAlmostEqual(area_extent[2],
                               PROJ_KM['gdal_xgeo_low_right'] / 1000.)
        self.assertAlmostEqual(area_extent[3],
                               PROJ_KM['gdal_ygeo_up_left'] / 1000.)

        # a, b and h in meters
        self.scn.nc.attrs = PROJ
        proj_str, area_extent = self.scn._get_projection()
        self.assertTrue('+units=m' in proj_str)
        self.assertAlmostEqual(area_extent[0], PROJ['gdal_xgeo_up_left'])
        self.assertAlmostEqual(area_extent[1], PROJ['gdal_ygeo_low_right'])
        self.assertAlmostEqual(area_extent[2], PROJ['gdal_xgeo_low_right'])
        self.assertAlmostEqual(area_extent[3], PROJ['gdal_ygeo_up_left'])

    def test_scale_dataset_attr_removal(self):
        """Test the scaling of the dataset and removal of obsolete attributes."""
        import numpy as np
        import xarray as xr

        attrs = {'scale_factor': np.array(10),
                 'add_offset': np.array(20)}
        var = xr.DataArray([1, 2, 3], attrs=attrs)
        var = self.scn.scale_dataset('dummy', var, 'dummy')
        np.testing.assert_allclose(var, [30, 40, 50])
        self.assertNotIn('scale_factor', var.attrs)
        self.assertNotIn('add_offset', var.attrs)

    def test_scale_dataset_floating(self):
        """Test the scaling of the dataset with floating point values."""
        import numpy as np
        import xarray as xr
        attrs = {'scale_factor': np.array(1.5),
                 'add_offset': np.array(2.5),
                 '_FillValue': 1}
        var = xr.DataArray([1, 2, 3], attrs=attrs)
        var = self.scn.scale_dataset('dummy', var, 'dummy')
        np.testing.assert_allclose(var, [np.nan, 5.5, 7])
        self.assertNotIn('scale_factor', var.attrs)
        self.assertNotIn('add_offset', var.attrs)

        attrs = {'scale_factor': np.array(1.5),
                 'add_offset': np.array(2.5),
                 'valid_min': 1.1}
        var = xr.DataArray([1, 2, 3], attrs=attrs)
        var = self.scn.scale_dataset('dummy', var, 'dummy')
        np.testing.assert_allclose(var, [np.nan, 5.5, 7])
        self.assertNotIn('scale_factor', var.attrs)
        self.assertNotIn('add_offset', var.attrs)

        attrs = {'scale_factor': np.array(1.5),
                 'add_offset': np.array(2.5),
                 'valid_max': 2.1}
        var = xr.DataArray([1, 2, 3], attrs=attrs)
        var = self.scn.scale_dataset('dummy', var, 'dummy')
        np.testing.assert_allclose(var, [4, 5.5, np.nan])
        self.assertNotIn('scale_factor', var.attrs)
        self.assertNotIn('add_offset', var.attrs)

        attrs = {'scale_factor': np.array(1.5),
                 'add_offset': np.array(2.5),
                 'valid_range': (1.1, 2.1)}
        var = xr.DataArray([1, 2, 3], attrs=attrs)
        var = self.scn.scale_dataset('dummy', var, 'dummy')
        np.testing.assert_allclose(var, [np.nan, 5.5, np.nan])
        self.assertNotIn('scale_factor', var.attrs)
        self.assertNotIn('add_offset', var.attrs)


def suite():
    """Test suite for test_writers."""
    loader = unittest.TestLoader()
    my_suite = unittest.TestSuite()
    my_suite.addTest(loader.loadTestsFromTestCase(TestNcNWCSAF))

    return my_suite


if __name__ == '__main__':
    unittest.main()
