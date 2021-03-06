# Copyright 2012-2014 by the MicroMagnum Team
# Copyright 2014 by the magnum.fd Team
#
# This file is part of magnum.fd.
# magnum.fd is based heavily on MicroMagnum.
# (https://github.com/MicroMagnum/MicroMagnum)
#
# magnum.fd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# magnum.fd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with magnum.fd. If not, see <http://www.gnu.org/licenses/>.

from magnum.micromagnetics.world.shape import Shape

from magnum.logger import logger
from magnum.mesh import RectangularMesh
from math import log, floor

try:
    import gmshpy
    _found_gmsh_lib = True
except:
    _found_gmsh_lib = False
    logger.warn("Python wrappers for Gmsh not found!")
    logger.warn("-> This means that the GmshShape class is not available!")

class GmshShape(Shape):
    """
    This class can create a shape from a number of gemetry/mesh files that are supported by Gmsh.
    The Python wrappers for Gmsh have to be installed on the system.
    """
    def __init__(self, model, shift = (0.0, 0.0, 0.0), scale = 1.0):
        if not _found_gmsh_lib: raise NotImplementedError("GmshShape class can not be used because the Python wrappers for GMSH could not be loaded ('import gmshpy')")
        super(GmshShape, self).__init__()

        self.__model = model
        self.__shift = shift
        self.__scale = scale

    def isPointInside(self, pt):
        spt = gmshpy.SPoint3(
            pt[0] / self.__scale + self.__shift[0],
            pt[1] / self.__scale + self.__shift[1],
            pt[2] / self.__scale + self.__shift[2])
        return self.__model.getMeshElementByCoord(spt)

    @staticmethod
    def with_mesh_from_file(filename, cell_size, scale = 1.0, lc = None, order = 3):
        """
        Creates a shape from a Gmsh supported file format (e.g. brep, msh) along
        with a suitabe :class:`RectangularMesh` to fit the shape in.

        *Arguments*
          filename (:class:`string`)
            The geometry file to import
          cell_size (:class:`[float]`)
            Cell size of the target mesh to be created
          scale (:class:`float`)
            Scaling of the input file
          lc (:class:`float`)
            Discretization constant for geometry approximation.
            Don't use this unless you know what you are doing.
          order (:class:`int`)
            Order for geometry approximiation.
            Don't use this unless you know what you are doing.

        *Returns*
          :class:`[Mesh, Shape]`
            The mesh and the shape
        """
        if not _found_gmsh_lib: raise NotImplementedError("GmshShape class can not be used because the Python wrappers for GMSH could not be loaded ('import gmshpy')")

        # Create GMSH model
        model = gmshpy.GModel()
        model.setFactory("Gmsh")
        model.load(filename)

        # mesh if not already meshed
        if model.getMeshStatus() < 3:
          if lc == None:
            lc = min(cell_size) / scale * order * 2
          vertices = model.bindingsGetVertices()
          for v in vertices:
            v.setPrescribedMeshSizeAtVertex(lc)
          model.mesh(3)
          model.setOrderN(order, 0, 0)

        # get bounds
        bounds = model.bounds()
        p1 = (bounds.min().x(), bounds.min().y(), bounds.min().z())
        p2 = (bounds.max().x(), bounds.max().y(), bounds.max().z())

        # Create Rectangular Mesh
        num_nodes = [int(round((b-a)/c*scale)) for a,b,c in zip(p1, p2, cell_size)]
        mesh = RectangularMesh(num_nodes, cell_size)

        return mesh, GmshShape(model, p1, scale)
