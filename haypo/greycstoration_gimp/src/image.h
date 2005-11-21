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

#ifndef GREYCSTORATION_IMAGE_H
#define GREYCSTORATION_IMAGE_H
//----------------------------------------------------------------------------
#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>
//----------------------------------------------------------------------------

class Image
{
public:
	GimpDrawable *drawable;   /* Current image */
	GimpPixelRgn src_rgn, dst_rgn;
	gint       sel_x1;               /* Selection bounds */
	gint       sel_y1;
	gint       sel_x2;
	gint       sel_y2;
	gint       sel_width;            /* Selection width */
	gint       sel_height;           /* Selection height */
	gint       img_bpp;              /* Bytes-per-pixel in image */
	bool		img_alpha;
	guint		width;
	bool		is_preview;
	GimpPreview*	preview;
	bool 		use_progress;
	GimpRunMode run_mode;
public:
	Image();
	void init(GimpDrawable *drawable, GimpPreview *preview);
};

extern Image image;
//----------------------------------------------------------------------------
#endif
