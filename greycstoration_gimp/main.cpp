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

#include <libgimp/gimp.h>
#include "plug_in.h"
#include "dialog.h"
#include "greycstoration.h"
#include <unistd.h>

//----------------------------------------------------------------------------
GREYCstoration greyc;
GREYCstoration_params greyc_params;
Image image;
//----------------------------------------------------------------------------

static void query(void);
static void run (const gchar* name,
		gint nparams,
		const GimpParam* param,
		gint* nreturn_vals,
		GimpParam** return_vals);

//----------------------------------------------------------------------------

GimpPlugInInfo PLUG_IN_INFO = 
{
	NULL,
	NULL,
	query,
	run
};

//----------------------------------------------------------------------------

MAIN()

//----------------------------------------------------------------------------

static void query(void)
{
	static GimpParamDef args[] =
	{
		{
			GIMP_PDB_INT32,
			"run_mode",
			"Run mode"
		},{
			GIMP_PDB_IMAGE,
			"image",
			"Input image"
		},{
			GIMP_PDB_DRAWABLE,
			"drawable",
			"Input drawable"
		}
	};
	gimp_install_procedure (
			"plug_in_hello",
			PLUG_IN_NAME,
			"Filtre Greystoration",
			"Victor STINNER",
			"Copyright Victor STINNER",
			"2005",
			"<Image>/Filters/Misc/_GREYCstoration",
			"RGB*", //GRAY*
			GIMP_PLUGIN,
			G_N_ELEMENTS(args), 0,
			args, NULL);
}

//----------------------------------------------------------------------------

static void run (const gchar* name,
		gint nparams,
		const GimpParam* param,
		gint* nreturn_vals,
		GimpParam** return_vals)
{
	static GimpParam values[1];
	GimpPDBStatusType status = GIMP_PDB_SUCCESS;

	/* Reduce the processes importance so that it doesn't make the computer 
	   non-interactive */
	nice(19);

	/* Mise en place d'une valeur obligatoire de retour */
	*nreturn_vals = 1;
	*return_vals = values;

	values[0].type = GIMP_PDB_STATUS;
	values[0].data.d_status = status;

	image.run_mode = static_cast<GimpRunMode> (param[0].data.d_int32);
	GimpDrawable *drawable = gimp_drawable_get (param[2].data.d_drawable);
	
	switch (image.run_mode)
	{
		case GIMP_RUN_INTERACTIVE:
			gimp_get_data("plug_in_" PLUG_IN_NAME, &greyc_params);
			if (!dialog(greyc_params, drawable)) return;
			gimp_set_data("plug_in_" PLUG_IN_NAME, &greyc_params, sizeof(greyc_params));
			break;
			
		case GIMP_RUN_NONINTERACTIVE:
return;
			break;

		case GIMP_RUN_WITH_LAST_VALS:
			gimp_get_data("plug_in_" PLUG_IN_NAME, &greyc_params);
			break;
		default: return;
	}

	if (!DoGREYCstoration(NULL, drawable)) 
	{
		if (image.run_mode != GIMP_RUN_NONINTERACTIVE)
			g_message ("Erreur !?");
		status = GIMP_PDB_EXECUTION_ERROR;
		values[0].data.d_status = status;
	}
	gimp_drawable_detach (drawable);
}

//----------------------------------------------------------------------------

