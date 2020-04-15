import os
import json
from pathlib import Path
from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint, Response, safe_join
from shotglass2.users.admin import login_required, table_access_required
from shotglass2.shotglass import get_site_config
from shotglass2.takeabeltof.utils import render_markdown_for, printException, handle_request_error, send_static_file, \
    cleanRecordID
from shotglass2.takeabeltof.date_utils import datetime_as_string, local_datetime_now
from bikematch.models import Folks
from datetime import date

mod = Blueprint('folks',__name__, template_folder='templates/', url_prefix='/folks')


def setExits():
    g.listURL = url_for('.display')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'Folks'


@mod.route('/', methods=['POST', 'GET',])
@table_access_required(Folks)
def display():
    """List folks records """
    
    setExits()
    g.title = "Folks Records"
    recs = Folks(g.db).select()
    
    return render_template('bikematch/folks/folks_list.html',recs=recs)
    
        
@mod.route('/edit/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/edit/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/edit', methods=['POST', 'GET',])
@mod.route('/edit/', methods=['POST', 'GET',])
@table_access_required(Folks)
def edit(rec_id=None):
    """Edit or create folks records"""
    from app import app
    
    # import pdb;pdb.set_trace()
    
    setExits()
    g.title = "Edit Folks Record"
    site_config = get_site_config()
    rec_id = cleanRecordID(request.form.get('id',rec_id))
    if rec_id < 0:
        flash('Invalid Folks ID')
        return redirect(g.listURL)
    folks = Folks(g.db)
    if rec_id == 0:
        rec = folks.new()
        rec.date_created = date.today()
    else:
        rec = Folks(g.db).get(rec_id)
    
    if rec and request.form:
        folks.update(rec,request.form)
        folks.save(rec,commit=True)

        return redirect(g.listURL)

        
    return render_template('bikematch/folks/folks_edit.html',rec=rec)
        
@mod.route('/delete/<int:rec_id>', methods=['POST', 'GET',])
@mod.route('/delete/<int:rec_id>/', methods=['POST', 'GET',])
@mod.route('/delete', methods=['POST', 'GET',])
@mod.route('/delete/', methods=['POST', 'GET',])
@table_access_required(Folks)
def delete(rec_id=None):
    """Delete folks records"""
    from app import app
    setExits()
    g.title = "Delete Folks Record"
    # import pdb;pdb.set_trace()
    rec_id = cleanRecordID(rec_id)
    folks = Folks(g.db)
    folks.delete(rec_id,commit=True)
        
    return redirect(g.listURL)
        


