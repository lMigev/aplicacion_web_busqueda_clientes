from flask import Blueprint, jsonify, render_template, request, send_file
from models.database import Contact, SearchHistory, db
from sqlalchemy import func
import pandas as pd
import io
import datetime

clients_bp = Blueprint('clients_bp', __name__)

@clients_bp.route('/clientes', methods=['GET'])
def clientes_page():
    return render_template('clientes.html')

@clients_bp.route('/api/clientes', methods=['GET'])
def get_clientes():
    # Permitir filtros opcionales por nombre, email, etc.
    name = request.args.get('name', '').strip().lower()
    email = request.args.get('email', '').strip().lower()
    min_quality = request.args.get('min_quality', '').strip()
    query = Contact.query
    if name:
        query = query.filter(Contact.name.ilike(f'%{name}%'))
    if email:
        query = query.filter(Contact.email.ilike(f'%{email}%'))
    if min_quality and min_quality.isdigit():
        query = query.filter(Contact.quality_score >= int(min_quality))
    clientes = query.order_by(Contact.created_at.desc()).all()
    return jsonify([c.to_dict() for c in clientes])

@clients_bp.route('/api/clientes/export', methods=['GET'])
def export_clientes():
    name = request.args.get('name', '').strip().lower()
    email = request.args.get('email', '').strip().lower()
    min_quality = request.args.get('min_quality', '').strip()
    query = Contact.query
    if name:
        query = query.filter(Contact.name.ilike(f'%{name}%'))
    if email:
        query = query.filter(Contact.email.ilike(f'%{email}%'))
    if min_quality and min_quality.isdigit():
        query = query.filter(Contact.quality_score >= int(min_quality))
    clientes = query.order_by(Contact.created_at.desc()).all()
    data = [c.to_dict() for c in clientes]
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='clientes_exportados.csv'
    )

@clients_bp.route('/estadisticas', methods=['GET'])
def estadisticas_page():
    return render_template('estadisticas.html')

@clients_bp.route('/api/estadisticas', methods=['GET'])
def api_estadisticas():
    # Total de contactos
    total_contactos = Contact.query.count()
    # Calidad promedio
    calidad_promedio = round(Contact.query.with_entities(func.avg(Contact.quality_score)).scalar() or 0, 2)
    # Total de búsquedas
    total_busquedas = db.session.query(SearchHistory).count()
    # Contactos por mes (últimos 12 meses)
    hoy = datetime.datetime.utcnow()
    labels = []
    data = []
    for i in range(11, -1, -1):
        mes = (hoy - datetime.timedelta(days=30*i)).strftime('%Y-%m')
        labels.append(mes)
        inicio = (hoy - datetime.timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i == 0:
            fin = hoy
        else:
            fin = (hoy - datetime.timedelta(days=30*(i-1))).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = Contact.query.filter(Contact.created_at >= inicio, Contact.created_at < fin).count()
        data.append(count)
    return jsonify({
        'total_contactos': total_contactos,
        'calidad_promedio': calidad_promedio,
        'total_busquedas': total_busquedas,
        'contactos_por_mes': {
            'labels': labels,
            'data': data
        }
    })
