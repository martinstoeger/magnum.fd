# Copyright 2012-2014 by the MicroMagnum Team
# Copyright 2014 by the magnum.fd Team
#
# This file is part of magnum.fd.
# magnum.fd is based heavily on MicroMagnum.
# (https://github.com/MicroMagnum/MicroMagnum)
# (at your option) any later version.
#
# magnum.fd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with magnum.fd. If not, see <http://www.gnu.org/licenses/>.

import sys

from magnum.micromagnetics.stephandler.screen_log import ScreenLog


class ScreenLogMinimizer(ScreenLog):
    """
    This step handler produces a log of the minimization on the screen.
    """

    def __init__(self):
        super(ScreenLog, self).__init__(sys.stdout)
        self.addColumn(("step", "step", "", "%d"), lambda state: state.step)
        self.addEnergyColumn("E_tot")
        self.addWallTimeColumn()
        self.addColumn(("deg_per_ns", "deg_per_ns", "deg/ns", "%r"), lambda state: state.deg_per_ns_minimizer)
