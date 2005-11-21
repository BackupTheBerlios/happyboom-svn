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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "image.h"
//----------------------------------------------------------------------------

Image::Image()
{
	drawable = NULL;
	run_mode = GIMP_RUN_NONINTERACTIVE;
}

//----------------------------------------------------------------------------

void Image::init(GimpDrawable *pdrawable, GimpPreview *ppreview)
{
	drawable = pdrawable;
	preview = ppreview;
	if (ppreview) {
		is_preview = true;
		gimp_preview_get_position(preview, &sel_x1, &sel_y1);
		gimp_preview_get_size(preview, &sel_width, &sel_height);
		sel_x2 = sel_x1 + sel_width;	
		sel_y2 = sel_y1 + sel_height;	
	} else {
		is_preview = false;
		gimp_drawable_mask_bounds (drawable->drawable_id,
				&sel_x1, &sel_y1, &sel_x2, &sel_y2);
		sel_width  = sel_x2 - sel_x1;
		sel_height = sel_y2 - sel_y1;
	}
	img_bpp   = gimp_drawable_bpp (drawable->drawable_id);
	img_alpha = gimp_drawable_has_alpha (drawable->drawable_id);
	gimp_pixel_rgn_init (&src_rgn, drawable,
			sel_x1, sel_y1, sel_width, sel_height, FALSE, FALSE);
	gimp_pixel_rgn_init (&dst_rgn, drawable,
			sel_x1, sel_y1, sel_width, sel_height, !is_preview, TRUE);
	width = sel_width * img_bpp;
	use_progress = (run_mode != GIMP_RUN_NONINTERACTIVE) && !is_preview;
}

//----------------------------------------------------------------------------
