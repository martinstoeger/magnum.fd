/*
 * Copyright 2012-2014 by the MicroMagnum Team
 * Copyright 2014 by the magnum.fd Team
 *
 * This file is part of magnum.fd.
 * magnum.fd is based heavily on MicroMagnum.
 * (https://github.com/MicroMagnum/MicroMagnum)
 * 
 * magnum.fd is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * magnum.fd is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with magnum.fd. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef TRANSPOSE_UNPAD_H
#define TRANSPOSE_UNPAD_H

// XYZ -> ZxY
void cuda_transpose_unpad_c2c(
	int dim_x, int dim_y, int dim_z, // input size
	int red_x, // red_x <= dim_x
	const float *in_x, const float *in_y, const float *in_z,  // size: dim_x * dim_y * dim_z
	      float *out_x,     float *out_y,      float *out_z); // size: dim_z * red_x * dim_y (cut in x-direction [of input] from dim_x->red_x)

// XYZ -> ZxY, scalar version
void cuda_transpose_unpad_c2c(
	int dim_x, int dim_y, int dim_z, // input size
	int red_x, // red_x <= dim_x
	const float *in,  // size: dim_x * dim_y * dim_z
	      float *out); // size: dim_z * red_x * dim_y (cut in x-direction [of input] from dim_x->red_x)

#endif
