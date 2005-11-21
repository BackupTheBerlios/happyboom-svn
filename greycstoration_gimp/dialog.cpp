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

#include "plugin-intl.h"

#include <stdio.h>

#include "dialog.h"
//----------------------------------------------------------------------------
#include "image.h"
#include "greycstoration.h"
#include <libgimp/gimp.h>
#include <libgimp/gimpui.h>
#include <gtk/gtk.h>
//----------------------------------------------------------------------------
#define SCALE_WIDTH 125
#define SCALE_DIGITS 3
#define BOX_SPACING 6
//----------------------------------------------------------------------------

#define TABLE_SCALE(ROW, LABEL,TYPE,VALUE,MIN,MAX,DELTA1,DELTA2,DIGITS) \
    { GtkObject *scale = gimp_scale_entry_new ( \
			GTK_TABLE (table), 0, ROW, \
			LABEL, SCALE_WIDTH, 0, \
			VALUE, MIN, MAX, DELTA1, DELTA2, DIGITS, \
			TRUE, 0, 0, \
			NULL, NULL); \
	g_signal_connect (scale, "value_changed", \
			G_CALLBACK(gimp_##TYPE##_adjustment_update), &VALUE); \
	g_signal_connect_swapped (scale, "value_changed", \
			G_CALLBACK(gimp_preview_invalidate), preview); }

//----------------------------------------------------------------------------

GREYCstoration_params::GREYCstoration_params()
{
	nb_iter        = 1;
	dt             = 20.0f;
	sigma          = 1.4f;
	dlength        = 0.8;
	dtheta         = 45.0;
	onormalize     = false;
	power1         = 0.1;
	power2         = 0.9;
	gauss_prec     = 3.0f;
	linear         = true;
	onormalize     = false;
	preview        = true;
}

//----------------------------------------------------------------------------

GtkWidget* ajoute_param(
		GtkObject *spinbutton_adj, 
		GtkWidget *dst_box, 
		const char *label_string,
		int digits=0)
{
	GtkWidget *main_hbox;
	GtkWidget *param_label;
	GtkWidget *spinbutton;

	/* Boîte horizontale */
	main_hbox = gtk_hbox_new (FALSE, BOX_SPACING);
	gtk_widget_show (main_hbox);
	gtk_container_add (GTK_CONTAINER(dst_box), main_hbox);

	/* Paramètre : Texte */
	param_label = gtk_label_new_with_mnemonic(label_string);
	gtk_widget_show (param_label);
	gtk_box_pack_start(GTK_BOX(main_hbox), param_label, FALSE, FALSE, 6);
	gtk_label_set_justify (GTK_LABEL(param_label), GTK_JUSTIFY_RIGHT);

	/* Paramètre : SpinButton */	
	if (0 <= digits)
	{
		spinbutton = gtk_spin_button_new (GTK_ADJUSTMENT(spinbutton_adj), 1, digits);
		gtk_spin_button_set_numeric (GTK_SPIN_BUTTON(spinbutton), TRUE);
	} else {
		spinbutton = gtk_check_button_new();
	}
	gtk_widget_show (spinbutton);
	gtk_box_pack_start (GTK_BOX(main_hbox), spinbutton, FALSE, FALSE, 6);
	if (digits < 0) return spinbutton; else return NULL;
}

//----------------------------------------------------------------------------

void dialog_page1 (GREYCstoration_params &params, GtkWidget *notebook, GtkWidget *preview)
{
	GtkWidget *page_label;   
	GtkWidget *table;

	// Create the table
	table = gtk_table_new (5, 3, FALSE);
	gtk_table_set_col_spacings (GTK_TABLE (table), 6);
	gtk_table_set_row_spacings (GTK_TABLE (table), 6);
	gtk_container_set_border_width (GTK_CONTAINER (table), 12);
	gtk_widget_show (table);

	// Insert table in a new notebook page
	page_label = gtk_label_new (_("Restore"));
	gtk_notebook_append_page (GTK_NOTEBOOK (notebook), table, page_label);
	gtk_widget_show (table);
	
	// Power1
	TABLE_SCALE(0, _("_Detail factor (p1):"), float, params.power1, 0, 2, 0.1, 0.3, SCALE_DIGITS);
	TABLE_SCALE(1, _("_Gradient factor (p2):"), float, params.power2, 0, 100, 0.1, 1, SCALE_DIGITS);
	TABLE_SCALE(2, _("_Time step (dt):"), float, params.dt, 1, 300, 10, 25, SCALE_DIGITS);
	TABLE_SCALE(3, _("_Blur (sigma):"), float, params.sigma, 0, 10, 0.2, 1, SCALE_DIGITS);
	TABLE_SCALE(4, _("Blur _iterations (iter) :"), int, params.nb_iter, 1, 5, 1, 2, 0);
}

void dialog_page2 (GREYCstoration_params &params, GtkWidget *notebook, GtkWidget *preview)
{
	GtkWidget *page_label;   
	GtkWidget *vbox;
	GtkWidget *table;

	// New vbox
	page_label = gtk_label_new (_("Quality"));
	vbox = gtk_vbox_new (FALSE, BOX_SPACING);
	gtk_notebook_append_page (GTK_NOTEBOOK (notebook), vbox, page_label);
	gtk_widget_show (vbox);

	// linear checkbox
	GtkWidget* check = ajoute_param(NULL, vbox, _("Use linear interpolation:"), -1);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (check), params.linear);
	g_signal_connect (check, "toggled",
			G_CALLBACK(gimp_toggle_button_update), &params.linear);

	// normalize checkbox
	check = ajoute_param(NULL, vbox, _("Normalize picture to [0-255]:"), -1);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (check), params.onormalize);
	g_signal_connect (check, "toggled",
			G_CALLBACK(gimp_toggle_button_update), &params.onormalize);	

	// Create the table
	table = gtk_table_new (3, 3, FALSE);
	gtk_table_set_col_spacings (GTK_TABLE (table), 6);
	gtk_table_set_row_spacings (GTK_TABLE (table), 6);
	gtk_container_set_border_width (GTK_CONTAINER (table), 12);
	gtk_widget_show (table);

	// Insert table in the container
	gtk_container_add (GTK_CONTAINER(vbox), table);
	gtk_widget_show (table);

	// Insert parameters into the table
	TABLE_SCALE(0, _("_Angular step (da):"), float, params.dtheta, 5, 90, 5, 15, SCALE_DIGITS);
	TABLE_SCALE(1, _("_Integral step (dt):"), float, params.dlength, 0.1, 10, 0.1, 0.5, SCALE_DIGITS);
	TABLE_SCALE(2, _("_Gaussian precision (gauss):"), float, params.gauss_prec, 0.1, 10, 0.1, 0.5, SCALE_DIGITS);	
}


//----------------------------------------------------------------------------

bool dialog(GREYCstoration_params &params, GimpDrawable *preview_src)
{
	GtkWidget *dialog;
	GtkWidget *notebook;
	GtkWidget *preview;
	GtkWidget *main_vbox;

	// New dialog
	gimp_ui_init (PLUGIN_NAME, false);
	dialog = gimp_dialog_new(
			_("GREYCstoration"), 
			PLUGIN_NAME,
			NULL, (GtkDialogFlags)0,
			gimp_standard_help_func, "plug-in-" PLUGIN_NAME,
			GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
			GTK_STOCK_OK,     GTK_RESPONSE_OK,
			NULL);

	// Main vbox	
	main_vbox = gtk_vbox_new (false, BOX_SPACING);
	gtk_container_add (GTK_CONTAINER(GTK_DIALOG(dialog)->vbox), main_vbox);
	gtk_widget_show (main_vbox);

	// Add preview 
	preview = gimp_drawable_preview_new(preview_src, &params.preview);
	gtk_container_add (GTK_CONTAINER(main_vbox), preview);
	gtk_widget_show (preview);
	g_signal_connect (preview, "invalidated",
			G_CALLBACK(DoGREYCstoration), preview_src);

	// Create notebook
	notebook = gtk_notebook_new ();
	gtk_notebook_set_tab_pos (GTK_NOTEBOOK (notebook), GTK_POS_TOP);
	gtk_container_add (GTK_CONTAINER (main_vbox), notebook);
	gtk_widget_show (notebook);

	// Create differents notebook pages
	dialog_page1(params, notebook, preview);
	dialog_page2(params, notebook, preview);

	// Display dialog 
	gtk_widget_show(dialog);
	gboolean run = gimp_dialog_run(GIMP_DIALOG(dialog)) == GTK_RESPONSE_OK;
	gtk_widget_destroy(dialog);
	return run;
}

//----------------------------------------------------------------------------

void process_flush()
{
	if (image.is_preview) {
		gimp_drawable_preview_draw_region(
				GIMP_DRAWABLE_PREVIEW(image.preview), 
				&image.dst_rgn);
	} else {
		gimp_drawable_flush (image.drawable);
		gimp_drawable_merge_shadow (image.drawable->drawable_id, TRUE);
		gimp_drawable_update (image.drawable->drawable_id,
				image.sel_x1, image.sel_y1, image.sel_width, image.sel_height);
		if (image.run_mode != GIMP_RUN_NONINTERACTIVE) gimp_displays_flush ();
	}
}

//----------------------------------------------------------------------------

void set_params()
{
#define SET(X) greyc.X = greyc_params.X
	SET(sigma);
	SET(nb_iter);
	SET(dt);
	SET(dlength);
	SET(power1);
	SET(power2);
	SET(onormalize);
	SET(gauss_prec);
	SET(linear);
#undef SET
}

//----------------------------------------------------------------------------

bool DoGREYCstoration(GimpPreview *preview, GimpDrawable *drawable)
{
	if (!gimp_drawable_is_rgb (drawable->drawable_id)) return false;
	if (image.run_mode != GIMP_RUN_NONINTERACTIVE) 
		gimp_progress_update (0);
	image.init(drawable, preview);
	set_params();
	greyc.load_picture(image);
	if (!greyc.process()) return false;
	greyc.store_picture(image);
	process_flush();	
	return true;
}

//----------------------------------------------------------------------------

