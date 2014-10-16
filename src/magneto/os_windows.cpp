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

#include "config.h"
#include <windows.h>

#include "Logger.h"

namespace os {

std::string pathSeparator()
{
	return "\\";
}

double getTickCount()
{
	// NOTE: The GetSystemTimeAsFileTime resolution can be as low as 15ms!

	FILETIME ft;
	GetSystemTimeAsFileTime(&ft);

	unsigned __int64 tmp = 0; // unit: 1e-7 seconds
	tmp |= ft.dwHighDateTime;
	tmp <<= 32;
	tmp |= ft.dwLowDateTime;

	return static_cast<double>(tmp * 1e-4); // convert to ms
}

bool disable_SSE_for_FFTW()
{
#ifdef _WIN64
	return false;
#else
	// Disable SSE for Windows 32-bit builds.
	return true;
#endif
}

} // namespace os
