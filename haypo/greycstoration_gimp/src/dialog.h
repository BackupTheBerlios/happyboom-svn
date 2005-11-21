/* GREYCstoration Gimp plugin
 * Copyright (C) 2005 Victor Stinner and David Tschumperlé
 *
 * This plug-in is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef GREYCSTORATION_DIALOG_H
#define GREYCSTORATION_DIALOG_H
//----------------------------------------------------------------------------
#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>
//----------------------------------------------------------------------------

typedef struct GREYCstoration_params
{
	gint nb_iter; // Number of smoothing iterations
	gfloat dt;       // Time step
	gfloat dlength; // Integration step
	gfloat dtheta; // Angular step (in degrees)
	gfloat sigma;  // Structure tensor blurring
	gfloat power1; // Diffusion limiter along isophote
	gfloat power2; // Diffusion limiter along gradient
	gfloat gauss_prec; //  Precision of the gaussian function
	gboolean onormalize; // Output image normalization (in [0,255])
	gboolean linear; // Use linear interpolation for integration ?
	gboolean preview; // Use preview ?
	GREYCstoration_params();
} GREYCstoration_params;

extern GREYCstoration_params greyc_params;

//----------------------------------------------------------------------------

bool dialog(GREYCstoration_params &params, GimpDrawable *drawable);

bool DoGREYCstoration(GimpPreview *preview, GimpDrawable *drawable);
//----------------------------------------------------------------------------
#endif
